import copy
import datetime
import os.path
import pickle
import pytz
import re
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/tasks']
TOKEN_FILE = os.path.join(os.path.split(__file__)[0], 'credentials', 'token.pickle')
CREDENTIALS_FILE = os.path.join(os.path.split(__file__)[0], 'credentials', 'credentials.json')
TIMEZONE = 'Europe/Amsterdam'
GOOGLE_TASKS_INBOX_ID = 'insert_inbox_ID_here'  # use `Inbox.get_lists`
GOOGLE_TASKS_WAITING_LIST_ID = 'insert_waiting_list_ID_here'  # use `Inbox.get_lists`


class Task:
    def __init__(self, identifier, title):
        self.ID = identifier
        self.title = title

    def __repr__(self):
        return self.title

    def __eq__(self, other):
        if self.title != other.title:
            return False
        elif self.ID != other.ID:
            return False
        return True


class GoogleAPI:
    def _setup_credentials(self):
        self._creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                self._creds = pickle.load(token)

        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                self._creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self._creds, token)

    def _setup_service(self, service, version):
        self._service = build(service, version, credentials=self._creds)


def _check_task_exists(f):
    def rf(self, *args, **kwargs):
        if not self.current_task:
            raise ValueError('No task is selected')
        f(self, *args, **kwargs)
    return rf


LIST_IDS = {
    'inbox': GOOGLE_TASKS_INBOX_ID,
    'waiting': GOOGLE_TASKS_WAITING_LIST_ID
}


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


class Calendar(GoogleAPI):
    def __init__(self):
        self._setup_credentials()
        self._setup_service('calendar', 'v3')
        self._query_days = 60

    def schedule_event(self, title, year, month, day):
        """
        Schedule an all-day event on a date determined by `year`, `month` and `day` with a `title`

        Args:
            title (string): the title of the event
            year (int): year to schedule the event
            month (int): month to schedule the event
            day (int): day to schedule the event
        """
        date_format = '{:0>4d}-{:0>2d}-{:0>2d}'
        event = {'start': {'date': date_format.format(year, month, day)},
                 'end': {'date': date_format.format(year, month, day)},
                 'summary': title}

        self._service.events().insert(calendarId="primary",
                                      body=event).execute()
            # TODO notification time is defaulted to 23:30 because of internal defaults. Circumvent this and take user defaults.

    def get_unfinished_tasks(self):
        """
        Tasks are unfinished when they
          - are daily: they are on the top of the calendar, and they
          - don't start with 'OK ' or 'K '
        """
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        past = (datetime.datetime.utcnow() -
                datetime.timedelta(days=self._query_days)
                ).isoformat() + 'Z'

        events_result = self._service.events().list(calendarId='primary',
                                                    timeMax=now, timeMin=past, maxResults=2000,
                                                    singleEvents=True).execute()  # singleEvents so that we have the 'start' field
        events = events_result.get('items', [])

        return [Task(x['id'], x['summary']) for x in events if
                'date' in x['start'] and
                x['summary'][:2] != "K " and
                x['summary'][:3] != "OK "]

    def change_title_with_prefix(self, task, prefix="OK "):
        """
        When tasks are done or moved, they don't get deleted. To prevent loss of events, the events only get renamed.
        """
        new_title = prefix+task.title
        edit = {'summary': new_title}
        self._service.events().patch(calendarId="primary", eventId=task.ID,
                                     body=edit).execute()


class Console:
    def __init__(self):
        self._inbox = Inbox()
        self._calendar = Calendar()
        self._define_input_handlers()
        self._define_weekday_mapping()
        self._day_end_hour = 3  # if time is before this hour, consider it as the previous day

    def _define_input_handlers(self):
        self._input_handlers = [  # regex on the left, function to call on the right
            (r'c(?: )?(\d*)((?:mon)|(?:tue)|(?:wed)|(?:thu)|(?:fri)|(?:sat)|(?:sun)|)$', self._reschedule_task),
            (r'd$', self._delete_task),
            (r'w$', self._task_to_waiting),
            (r's$', self._skip_task),
            (r'vi$', self._list_to_inbox),
            (r'vw$', self._list_to_waiting),
            (r'h$', self._view_help),
            (r'q$', self._quit),
            (r'p$', self.process_calendar_to_inbox),
            (r'n (.+)$', self._new_task),
            (r'e (.+)$', self._edit_task),
            (r'r$', self._reload_task)
        ]

    def _define_weekday_mapping(self):
        self._weekday_mapping = {
            'mon': 0,
            'tue': 1,
            'wed': 2,
            'thu': 3,
            'fri': 4,
            'sat': 5,
            'sun': 6
        }

    def _get_year_month_day(self, num_days_ahead=0):
        now = datetime.datetime.now(pytz.timezone(TIMEZONE))

        if now.hour < self._day_end_hour:  # previous day is intended early in the night
            now -= datetime.timedelta(days=1)

        now += datetime.timedelta(days=num_days_ahead)
        return now.year, now.month, now.day

    def _call_matching_handler(self, query):
        for regex, handler in self._input_handlers:
            match = re.match(regex, query)
            if not match:
                continue
            handler(*match.groups())
            return
        self._view_help()

    def _get_number_days_ahead_for_weekday(self, weekday, extra_weeks_ahead=0):
        """
        Args:
          weekday (str): the desired day of the week in the future in which this event is to be scheduled
          extra_weeks_ahead (int): how many weeks ahead this date is to be scheduled. Defaults to 0, or: the next occurrence of the weekday.
        """
        desired_weekday_number = self._weekday_mapping[weekday]
        current_weekday_number = datetime.datetime(*self._get_year_month_day()).weekday()
        days_to_go = (desired_weekday_number - current_weekday_number) % 7
        days_to_go = days_to_go + 7 if days_to_go == 0 else days_to_go  # we never intend the current day
        days_to_go += extra_weeks_ahead * 7
        return days_to_go

    def run(self):
        while True:
            print(self._inbox.get_task())
            query = input('productivity: ')
            self._call_matching_handler(query)

    def _reschedule_task(self, repetitions=1, day=None):
        repetitions = int(repetitions) if repetitions else 1

        if not day:  # interpret repetitions as the number of days in advance
            date = self._get_year_month_day(num_days_ahead=repetitions)
        else:  # interpret day as the weekday and repetitions as the extra number of weeks (one indexed)
            days_to_go = self._get_number_days_ahead_for_weekday(day, repetitions-1)
            date = self._get_year_month_day(num_days_ahead=days_to_go)

        self._calendar.schedule_event(self._inbox.get_task().title, *date)
        self._inbox.complete_task()

    def _delete_task(self):
        self._inbox.complete_task()

    def _task_to_waiting(self):
        self._inbox.move_task_to_list('waiting')

    def _skip_task(self):
        self._inbox.skip_task()

    def _list_to_inbox(self):
        self._inbox.set_current_list('inbox')

    def _list_to_waiting(self):
        self._inbox.set_current_list('waiting')

    def _view_help(self):
        with open(os.path.join(os.path.split(__file__)[0], 'README.md'), 'r') as f:
            print(f.read())
            print()

    def _quit(self):
        sys.exit()

    def process_calendar_to_inbox(self):
        self._inbox.set_current_list('inbox', force_reload=False)

        calendar_tasks = self._calendar.get_unfinished_tasks()
        for task in calendar_tasks:
            self._inbox.new_task(task.title, ignore_updating_locally=True)
            self._calendar.change_title_with_prefix(task)
        print(len(calendar_tasks), 'moved from calendar to inbox')

        self._inbox.set_current_list('previous', force_reload=False)

        if self._inbox.get_current_list() == 'inbox':
            self._inbox.get_tasks(force_reload=True)

    def _new_task(self, title):
        self._inbox.new_task(title=title)

    def _edit_task(self, new_title):
        self._inbox.edit_task(new_title)

    def _reload_task(self):
        self._inbox.get_tasks(force_reload=True)
