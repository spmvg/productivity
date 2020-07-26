import copy

from productivity.constants import LIST_IDS
from productivity.config import GOOGLE_TASKS_INBOX_ID
from productivity.task import Task
from productivity.google_api import GoogleAPI


def _check_task_exists(f):
    def rf(self, *args, **kwargs):
        if not self.current_task:
            raise ValueError('No task is selected')
        f(self, *args, **kwargs)
    return rf


class Inbox(GoogleAPI):
    def __init__(self):
        self._setup_credentials()
        self._setup_service('tasks', 'v1')
        self._set_hidden_variables()
        self._set_variables()

        self.get_tasks()

    def _set_hidden_variables(self):
        self._ignored_tasks = []
        self._current_list_id = GOOGLE_TASKS_INBOX_ID
        self._previous_list_id = GOOGLE_TASKS_INBOX_ID
        self._tasks = None

    def _set_variables(self):
        self.current_task = None

    def new_task(self, title, ignore_updating_locally=False):
        task = {'title': title}
        result = self._service.tasks().insert(tasklist=self._current_list_id, body=task).execute()

        if not ignore_updating_locally:
            self._tasks.append(Task(identifier=result['id'], title=title))

    def get_lists(self):
        lists = self._service.tasklists().list(maxResults=1000).execute().get('items', [])
        return lists

    def get_tasks(self, force_reload=False):
        """
        List the tasks in the inbox

        Args:
            force_reload (bool): if True, will reload the task list from the inbox using the Google Tasks API.
                If False, will only consult the Tasks API if the tasks have not yet been initialized.

        Returns:
            list(Task): list of tasks in the inbox
        """
        if self._tasks is None or force_reload:
            tasks = self._service.tasks().list(tasklist=self._current_list_id, maxResults=1000).execute().get('items', [])
            tasks = [task for task in tasks if task['status'] == 'needsAction']  # filter out recently completed
            self._tasks = [Task(identifier=task['id'], title=task['title']) for task in tasks]
        return self._tasks

    def get_task(self):
        for task in self.get_tasks():
            if task not in self._ignored_tasks:
                self.current_task = task
                return task

    @_check_task_exists
    def skip_task(self):
        self._ignored_tasks.append(self.current_task)

    @_check_task_exists
    def complete_task(self):
        self._service.tasks().patch(tasklist=self._current_list_id, task=self.current_task.ID,
                                    body={'status': 'completed'}).execute()

        self._tasks = [task for task in self._tasks if task != self.current_task]

    @_check_task_exists
    def edit_task(self, new_title):
        self._service.tasks().patch(tasklist=self._current_list_id, task=self.current_task.ID,
                                    body={'title': new_title}).execute()

        self.current_task.title = new_title

    def _get_list_id(self, task_list):
        task_id = LIST_IDS.get(task_list)
        if not task_id:
            raise ValueError("list {} should be in {}".format(task_list, list(LIST_IDS.keys())))
        return task_id

    def set_current_list(self, task_list, force_reload=True):
        """
        Sets the current list to the inbox or the waiting list.

        Args:
            task_list (str):
                `inbox` for the inbox
                `waiting` for the waiting list
                `previous` for the previous list value
            force_reload (bool): whether to reload the task list from Google Tasks. When set to False, reloading will not happen after calling this function, unless it is the first time requesting tasks.
        """
        if task_list == 'previous':
            if self._current_list_id == self._previous_list_id:
                return
            self._current_list_id, self._previous_list_id = copy.deepcopy(self._previous_list_id), copy.deepcopy(self._current_list_id)
        else:
            list_id = self._get_list_id(task_list)
            if self._current_list_id == list_id:
                return
            self._current_list_id, self._previous_list_id = list_id, copy.deepcopy(self._current_list_id)

        self.get_tasks(force_reload=force_reload)

    def get_current_list(self):
        for list_name, list_id in LIST_IDS.items():
            if list_id == self._current_list_id:
                return list_name

    @_check_task_exists
    def move_task_to_list(self, to_list):
        if self._current_list_id == self._get_list_id(to_list):
            print('Task "{}" is already in list {}'.format(self.current_task.title, to_list))
            return

        self.set_current_list(to_list, force_reload=False)
        self.new_task(self.current_task.title, ignore_updating_locally=True)
        self.set_current_list('previous', force_reload=False)
        self.complete_task()
