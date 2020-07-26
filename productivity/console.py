import datetime
import itertools
import os.path
import re
import sys
from functools import reduce

import pytz

from productivity.constants import WEEKDAY_TO_INT, INT_TO_WEEKDAY
from productivity.config import TIMEZONE, AVAILABLE_TIMES_PER_WEEKDAY
from productivity.datetime_interval import DatetimeInterval
from productivity.inbox_google import Inbox
from productivity.calendar_google import Calendar


class Console:
    def __init__(self):
        self._inbox = Inbox()
        self._calendar = Calendar()
        self._define_input_handlers()
        self._day_end_hour = 3  # if time is before this hour, consider it as the previous day

    def _define_input_handlers(self):
        self._input_handlers = [  # regex on the left, function to call on the right
            (r'c(?: )?(\d*)((?:mon)|(?:tue)|(?:wed)|(?:thu)|(?:fri)|(?:sat)|(?:sun)|)$', self._reschedule_task),
            (r'ci$', self.calendar_to_inbox),
            (r'd$', self._delete_task),
            (r'e (.+)$', self._edit_task),
            (r'h$', self._view_help),
            (r'ic$', self.inbox_to_calendar),
            (r'n (.+)$', self._new_task),
            (r'q$', self._quit),
            (r'r$', self._reload_task),
            (r's$', self._skip_task),
            (r'vi$', self._list_to_inbox),
            (r'vw$', self._list_to_waiting),
            (r'w$', self._task_to_waiting),
        ]

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
        desired_weekday_number = WEEKDAY_TO_INT[weekday]
        current_weekday_number = self._get_current_weekday_number()
        days_to_go = (desired_weekday_number - current_weekday_number) % 7
        days_to_go = days_to_go + 7 if days_to_go == 0 else days_to_go  # we never intend the current day
        days_to_go += extra_weeks_ahead * 7
        return days_to_go

    def _get_current_weekday_number(self):
        return datetime.datetime(*self._get_year_month_day()).weekday()

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

        self._calendar.schedule_event(self._inbox.get_task().title, datetime.datetime(*date))
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
        with open(os.path.join(os.path.split(__file__)[0], '..', 'README.md'), 'r') as f:
            print(f.read())
            print()

    def _quit(self):
        sys.exit()

    def calendar_to_inbox(self):
        self._inbox.set_current_list('inbox', force_reload=False)

        calendar_tasks = self._calendar.get_unfinished_tasks()
        for task in calendar_tasks:
            self._inbox.new_task(task.title, ignore_updating_locally=True)
            self._calendar.change_title_with_prefix(task)
        print(len(calendar_tasks), 'moved from calendar to inbox')

        self._inbox.set_current_list('previous', force_reload=False)

        if self._inbox.get_current_list() == 'inbox':
            self._inbox.get_tasks(force_reload=True)

    def inbox_to_calendar(self):
        self._inbox.set_current_list('inbox', force_reload=False)

        current_date = self._get_year_month_day()
        current_date_utc = pytz.timezone(TIMEZONE).localize(datetime.datetime(*current_date)).astimezone(pytz.UTC)
        tomorrow_utc = current_date_utc + datetime.timedelta(days=1)

        desired_intervals = self._desired_intervals_from_config(current_date, tomorrow_utc)

        whitespaces = self._determine_calendar_overlap_with_configured_times(current_date_utc, tomorrow_utc,
                                                                             desired_intervals)
        number_scheduled = self._schedule_in_whitespace(whitespaces)

        print(number_scheduled, 'tasks scheduled in calendar')
        self._inbox.set_current_list('previous', force_reload=False)

    def _schedule_in_whitespace(self, whitespaces):
        tasks = sorted(self._inbox.get_tasks(), key=lambda task: task.minutes(), reverse=True)
        number_scheduled = 0
        while tasks:
            task = tasks.pop()
            for whitespace in whitespaces:
                if task.minutes() >= whitespace.minutes():
                    continue

                start, end = whitespace.start, whitespace.start + datetime.timedelta(minutes=task.minutes())
                self._calendar.schedule_event(task.title, start, end)
                number_scheduled += 1
                break
            else:
                break

            whitespaces = DatetimeInterval.simplify(
                reduce(lambda a_list, another_list: a_list + another_list,
                       [interval.subtract([DatetimeInterval(start, end)]) for interval in whitespaces],
                       []))
        return number_scheduled

    def _determine_calendar_overlap_with_configured_times(self, current_date_utc, tomorrow_utc, desired_intervals):
        whitespace_in_calendar = self._calendar.whitespace(current_date_utc, tomorrow_utc)
        whitespaces = [
            intersected_interval for intersected_interval
            in map(lambda intervals: intervals[0].intersect(intervals[1]),
                   itertools.product(desired_intervals, whitespace_in_calendar))
            if intersected_interval
        ]
        return whitespaces

    def _desired_intervals_from_config(self, current_date, tomorrow_utc):
        current_weekday_number = self._get_current_weekday_number()
        current_weekday_name = INT_TO_WEEKDAY[current_weekday_number]
        desired_times_strings = AVAILABLE_TIMES_PER_WEEKDAY.get(current_weekday_name, [])
        desired_times = [
            (pytz.timezone(TIMEZONE).localize(datetime.datetime(*current_date,
                                                                int(start_str[:2]),
                                                                int(start_str[2:4]))).astimezone(pytz.UTC),
             pytz.timezone(TIMEZONE).localize(datetime.datetime(*current_date,
                                                                int(end_str[:2]),
                                                                int(end_str[2:4]))).astimezone(pytz.UTC))
            for start_str, end_str in desired_times_strings
        ]

        # discard intervals that are in the past
        interval_until_end_of_day = DatetimeInterval(datetime.datetime.now(tz=pytz.UTC), tomorrow_utc)
        desired_intervals = [
            interval for interval
            in (interval_until_end_of_day.intersect(DatetimeInterval(*start_end))
                for start_end in desired_times)
            if interval
        ]
        return desired_intervals

    def _new_task(self, title):
        self._inbox.new_task(title=title)

    def _edit_task(self, new_title):
        self._inbox.edit_task(new_title)

    def _reload_task(self):
        self._inbox.get_tasks(force_reload=True)
