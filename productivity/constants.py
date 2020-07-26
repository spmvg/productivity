import os.path

from productivity.config import GOOGLE_TASKS_INBOX_ID, GOOGLE_TASKS_WAITING_LIST_ID

LIST_IDS = {
    'inbox': GOOGLE_TASKS_INBOX_ID,
    'waiting': GOOGLE_TASKS_WAITING_LIST_ID
}

_WEEKDAY_INTS = [('mon', 0),
                 ('tue', 1),
                 ('wed', 2),
                 ('thu', 3),
                 ('fri', 4),
                 ('sat', 5),
                 ('sun', 6)]
WEEKDAY_TO_INT = dict(_WEEKDAY_INTS)
INT_TO_WEEKDAY = dict(reversed(weekday_int) for weekday_int in _WEEKDAY_INTS)

TOKEN_FILE = os.path.join(os.path.split(__file__)[0], '..', 'credentials', 'token.pickle')
CREDENTIALS_FILE = os.path.join(os.path.split(__file__)[0], '..', 'credentials', 'credentials.json')
SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/tasks']
