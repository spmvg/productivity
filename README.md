# productivity
Automates common tasks in Google Calendar and Google Tasks.
Based on the "Getting things done"-methodology.

### Setup
* Run `pip install -e .` in the current folder to install.
* Create Google Cloud OAuth credentials and put them in `credentials/credentials.json`.
* Set up the Google Tasks list IDs: `GOOGLE_TASKS_INBOX_ID = '...'` and `GOOGLE_TASKS_WAITING_LIST_ID = '...'` in `productivity/config.py`.
It is possible to use `Inbox.get_lists` to retrieve them.
* Run `run.py`.

### Options
* `c {REPETITIONS}{WEEKDAY}` puts the current task in the calendar as daily event.
    * `{REPETITIONS}` is an integer specifying the number of weeks to schedule ahead.
        * Defaults to 1, meaning: the next occurrence of `{WEEKDAY}`.
    * `{WEEKDAY}` is a string of either `mon`, `tue`, ..., `sun`.
        * Defaults to the day of tomorrow.
    * For example: `c 2sat` schedules the current task on the second Saturday from now.
* `ci` puts calendar all-day events from today or before, in the inbox.
* `d` marks a task as done.
* `e {TITLE}` edits the current task.
    * Example: `e My edited fancy title`.
* `h` displays help.
* `n {TITLE}` makes a new task.
    * Example: `n My fancy title`.
* `q` quits.
* `r` forces a reload of the list in Google Tasks.
    * Useful if the list in Google Tasks is manually edited while this tool is running.
* `s` skips the current task.
* `vi` sets the current list to the inbox.
* `vw` sets the current list to the waiting list.
* `w` moves current task to the waiting list.
