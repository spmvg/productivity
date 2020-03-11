# productivity
Automates common tasks in Google Calendar and Google Tasks.

### Setup
* Run `pip install -e .` in the current folder to install.
* Create Google Cloud OAuth credentials and put them in `credentials/credentials.json`.
* Run `run.py`.

### Options
* `n {TITLE}` makes a new task.
    * Example: `n My fancy title`.
* `e {TITLE}` edits the current task.
    * Example: `e My edited fancy title`.
* `c {REPETITIONS}{WEEKDAY}` puts the current task in the calendar as daily event.
    * `{REPETITIONS}` is an integer specifying the number of weeks to schedule ahead.
        * Defaults to 1, meaning: the next occurrence of `{WEEKDAY}`.
    * `{WEEKDAY}` is a string of either `mon`, `tue`, ..., `sun`.
        * Defaults to the day of tomorrow.
    * For example: `c 2sat` schedules the current task on the second Saturday from now.
* `d` marks a task as done.
* `w` moves current task to the waiting list.
* `s` skips the current task.
* `vi` sets the current list to the inbox.
* `vw` sets the current list to the waiting list.
* `p` processes all the calendar events from today or before and puts them in the inbox.
* `r` forces a reload of the list in Google Tasks.
    * Useful if the list in Google Tasks is manually edited while this tool is running.
* `h` displays help.
* `q` quits.
