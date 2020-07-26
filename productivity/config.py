TIMEZONE = 'Europe/Amsterdam'
GOOGLE_TASKS_INBOX_ID = 'insert_inbox_ID_here'  # use `Inbox.get_lists`
GOOGLE_TASKS_WAITING_LIST_ID = 'insert_waiting_list_ID_here'  # use `Inbox.get_lists`

# the console can schedule time in the calendar
DEFAULT_TASK_LENGTH = 7  # minutes, minutes that will be scheduled per inbox event
# inbox event will be scheduled within these intervals. Format: dict(str, list(tuple(str, str)))
AVAILABLE_TIMES_PER_WEEKDAY = {
    'mon': [('0000', '2359')],  # timestamp format: 'HHMM'
    'tue': [('0000', '2359')],
    'wed': [('0000', '2359')],
    'thu': [('0000', '2359')],
    'fri': [('0000', '2359')],
    'sat': [('0000', '2359')],
    'sun': [('0000', '2359')]
}
