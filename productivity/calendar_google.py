import datetime

import pytz

from productivity.datetime_interval import DatetimeInterval
from productivity.task import Task
from productivity.google_api import GoogleAPI


class Calendar(GoogleAPI):
    _RETURNED_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'  # returned by Google Calendar API list events
    _RFC_3339_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.0Z'  # used in Google Calendar API list events
    _YMD_DATE_FORMAT = '%Y-%m-%d'  # used for setting an all-day event in Google Calendar API
    _QUERY_DAYS = 60

    def __init__(self):
        self._setup_credentials()
        self._setup_service('calendar', 'v3')

    def schedule_event(self, title, start_datetime, end_datetime=None):
        """
        Schedule an event on a date with a title. This function can be used to schedule all-day events and events
        with a start- and end-date.

        Args:
            title (string): the title of the event
            start_datetime (datetime.datetime): start datetime of the event.
                If end_datetime is provided, then start_datetime is assumed to be in UTC.
                If end_datetime is not given, then the year, month and day of start_datetime will be used as-is.
            end_datetime (datetime.datetime, optional): end datetime of the event, assumed to be in UTC.
                If end_datetime is given, then the event is scheduled from start_datetime until end_datetime.
                If end_datetime is not provided, then the event is scheduled as an all-day event.
        """
        event = {'summary': title}
        if end_datetime:
            event['start'] = {'dateTime': start_datetime.strftime(self._RFC_3339_DATETIME_FORMAT)}
            event['end'] = {'dateTime': end_datetime.strftime(self._RFC_3339_DATETIME_FORMAT)}
        else:
            event['start'] = {'date': start_datetime.strftime(self._YMD_DATE_FORMAT)}
            event['end'] = event['start']

        # TODO: notification time defaults to 23:30 because of internal defaults. Circumvent this and take user default.
        self._service.events().insert(calendarId="primary", body=event).execute()

    def get_unfinished_tasks(self):
        """
        Tasks are unfinished when they
          - are daily: they are on the top of the calendar, and they
          - are not completed yet: they don't have the hashtag #done
        """
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        past = (datetime.datetime.utcnow() -
                datetime.timedelta(days=self._QUERY_DAYS)
                ).isoformat() + 'Z'

        events_result = self._service.events().list(calendarId='primary',
                                                    timeMax=now, timeMin=past, maxResults=2000,
                                                    singleEvents=True).execute()  # singleEvents for the 'start' field
        events = events_result.get('items', [])

        all_tasks = [Task(x['id'], x['summary']) for x in events if 'date' in x['start']]
        return [task for task in all_tasks if not task.is_done()]

    def whitespace(self, start_datetime_utc, end_datetime_utc):
        event_dicts = self._service.events().list(calendarId='primary', maxResults=2000,
                                                  timeMin=start_datetime_utc.strftime(Calendar._RFC_3339_DATETIME_FORMAT),
                                                  timeMax=end_datetime_utc.strftime(Calendar._RFC_3339_DATETIME_FORMAT),
                                                  singleEvents=True).execute().get('items', [])
        events = []
        for event_dict in event_dicts:
            event_start = event_dict.get('start', {}).get('dateTime')
            event_end = event_dict.get('end', {}).get('dateTime')
            if not event_start or not event_end:
                continue  # daily events don't have dateTime

            events.append(DatetimeInterval(start=Calendar.string_to_datetime(event_start).astimezone(pytz.UTC),
                                           end=Calendar.string_to_datetime(event_end).astimezone(pytz.UTC)))

        return DatetimeInterval(start_datetime_utc, end_datetime_utc).subtract(events)

    @classmethod
    def string_to_datetime(cls, datetime_string):
        datetime_string_without_semicolon_in_tz = datetime_string[:22] + datetime_string[23:25]
        return datetime.datetime.strptime(datetime_string_without_semicolon_in_tz, cls._RETURNED_DATETIME_FORMAT)

    def change_title_with_prefix(self, task):
        """
        When tasks are done or moved, they don't get deleted. To prevent loss of events, the events only get renamed.
        """
        task.complete()
        edit = {'summary': task.title}
        self._service.events().patch(calendarId="primary", eventId=task.ID, body=edit).execute()
