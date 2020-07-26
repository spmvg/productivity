import re

from productivity.config import DEFAULT_TASK_LENGTH


class Task:
    DONE_HASHTAG = '#done'
    _HASHTAG_REGEX = r'#[a-z0-9]+\b'
    _HASHTAG_MINUTES_REGEX = r'#([0-9]+)min\b'

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

    def tags(self):
        return re.findall(self._HASHTAG_REGEX, self.title.lower())

    def minutes(self):
        matching_minutes = re.search(self._HASHTAG_MINUTES_REGEX, self.title.lower())
        if not matching_minutes:
            return DEFAULT_TASK_LENGTH

        return int(matching_minutes.group(1))

    def is_done(self):
        return self.DONE_HASHTAG in self.tags()

    def complete(self):
        self.title = self.DONE_HASHTAG + ' ' + self.title
