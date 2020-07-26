# productivity
Automates common tasks in Google Calendar and Google Tasks.
Based on the "Getting things done"-methodology.

### Setup
* Run `pip install -e .` in the current folder to install.
* Create Google Cloud OAuth credentials and put them in `credentials/credentials.json`.
* Set up the Google Tasks list IDs: `GOOGLE_TASKS_INBOX_ID = '...'` and `GOOGLE_TASKS_WAITING_LIST_ID = '...'` in `config.py`.
It is possible to use `Inbox.get_lists` to retrieve them.
* Run `run.py`.

### Commands
* `c {REPETITIONS}{WEEKDAY}` puts the current task in the calendar as daily event.
    * `{REPETITIONS}` is an integer specifying the number of weeks to schedule ahead. Defaults to 1, meaning: the next occurrence of `{WEEKDAY}`.
    * `{WEEKDAY}` is a string of either `mon`, `tue`, ..., `sun`. Defaults to the day of tomorrow.
    * For example: `c 2sat` schedules the current task on the second Saturday from now.
* `ci` puts calendar all-day events from today or before, in the inbox.
These all-day events can originate from manual insertion in the calendar or usage of the `c` command.
Tasks that have been moved by `ci`, are indicated by the hashtag `#done` in the title.
The command `ci` is not the opposite of `ic`: see the help of `ic` below for more explanation.
* `d` marks a task as done.
* `e {TITLE}` edits the current task.  
Example: `e My edited fancy title`.
* `h` displays help.
* `ic` schedules tasks from the inbox in the calendar as non-daily events.
These non-daily calendar events are intended as suggestions for completing inbox tasks.
    * The command `ic` will only place a task in the calendar if
        1. there is no other event in the calendar at that time;
        2. the time is marked as available in the configuration `AVAILABLE_TIMES_PER_WEEKDAY` in `config.py`.
        This configuration indicates the times per weekday which are available for completing tasks.
        By default, the entire day is available.
    * The duration in minutes is determined by the configuration `DEFAULT_TASK_LENGTH` in `config.py`.
    If a hashtag is available in the title, the duration of the task in minutes will be overridden.
    For example, the hashtag `#15min` indicates that the calendar event has a duration of 15 minutes.
    * The command `ic` is not the opposite of `ci`.
    The command `ci` moves _daily_ events from the calendar to the inbox, while `ic` plans tasks in the calendar as _non-daily_ events.
    * Tasks in the inbox will not be removed by `ic`: the scheduled time is only a suggestion.
    If a calendar event scheduled by `ic` is ignored, the inbox task will not be forgotten.
* `n {TITLE}` makes a new task.  
Example: `n My fancy title`.
* `q` quits.
* `r` forces a reload of the list in Google Tasks. Useful if the list in Google Tasks is manually edited while this tool is running.
* `s` skips the current task.
* `vi` sets the current list to the inbox.
* `vw` sets the current list to the waiting list.
* `w` moves current task to the waiting list.
