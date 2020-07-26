from __future__ import annotations

import datetime
import functools
import numbers
from typing import List


@functools.total_ordering
class DatetimeInterval:
    _timezone_format = '%Y%m%dT%H%M'

    def __init__(self, start: datetime.datetime, end: datetime.datetime):
        if not isinstance(start, datetime.datetime) or not isinstance(end, datetime.datetime):
            raise ValueError('Start and end of DatetimeInterval must be of type datetime.datetime,'
                             ' not %s and %s, respectively.' % (type(start), type(end)))
        if start >= end:
            raise ValueError('Start datetime %s must be before end datetime %s' % (start, end))
        self.start = start
        self.end = end

    def __repr__(self):
        return (self.start.strftime(DatetimeInterval._timezone_format) +
                '-' +
                self.end.strftime(DatetimeInterval._timezone_format))

    def __eq__(self, other):
        if not isinstance(other, DatetimeInterval):
            raise ValueError('DatetimeInterval objects cannot be compared to objects of type %s' % type(other))
        return self.start == other.start and self.end == other.end

    def __lt__(self, other):
        if not isinstance(other, DatetimeInterval):
            raise ValueError('DatetimeInterval objects cannot be compared to objects of type %s' % type(other))
        return self.start < other.start

    def union(self, other: DatetimeInterval):
        """
        Takes the union of two DatetimeIntervals

        Returns: list(DatetimeInterval): union of the DatetimeIntervals. If the input DatetimeIntervals are disjoint,
            then there will be two DatetimeIntervals in the output. Otherwise, the result will be a list containing a
            single DatetimeInterval.
        """
        if not self.intersect(other) and not self.start == other.end and not self.end == other.start:
            return [self, other]

        return [DatetimeInterval(start=min(self.start, other.start),
                                 end=max(self.end, other.end))]

    def intersect(self, other: DatetimeInterval):
        """
        Finds the intersection between two DatetimeIntervals

        Returns:
            DatetimeInterval or None: the intersection between two DatetimeIntervals.
                If there is no intersection the result will be None
        """
        start_of_intersection = max(self.start, other.start)
        end_of_intersection = min(self.end, other.end)
        if start_of_intersection < end_of_intersection:
            return DatetimeInterval(start_of_intersection, end_of_intersection)

    def minutes(self) -> numbers.Number:
        return (self.end - self.start).total_seconds() / 60

    @staticmethod
    def simplify(intervals: List[DatetimeInterval]) -> List[DatetimeInterval]:
        """
        Reduces the overlap in a list of DatetimeIntervals to the minimum.

        Args:
            intervals (list(DatetimeInterval)): DatetimeIntervals to simplify

        Returns: list(DatetimeInterval): sorted DatetimeIntervals without pairwise overlap. The pairwise intersection
            between all elements is None.
        """
        if not intervals:
            return []

        sorted_intervals = sorted(intervals)
        interval_to_combine = sorted_intervals[0]
        results = []
        for interval in sorted_intervals[1:]:
            union = interval_to_combine.union(interval)
            if len(union) == 1:  # interval and interval_to_combine can be combined
                interval_to_combine = union[0]
            elif len(union) == 2:
                results.append(interval_to_combine)
                interval_to_combine = interval  # combining is not possible: update interval_to_combine
        results.append(interval_to_combine)
        return results

    def subtract(self, intervals: List[DatetimeInterval]) -> List[DatetimeInterval]:
        """
        Given self and a list of DatetimeIntervals, calculate DatetimeIntervals such that the union of returning
        DatetimeIntervals and the list of DatetimeIntervals is equal to self. In other words: calculate the "free
        space" between a list of DatetimeIntervals in the period given by self. The returned DatetimeIntervals are
        ordered by start date in ascending order.

        Args:
            intervals (list(DatetimeInterval)): DatetimeIntervals to subtract from self

        Returns: list(DatetimeInterval): DatetimeIntervals such that the union of the returned DatetimeIntervals and
            intervals is self.
        """
        intervals_with_boundary = ([DatetimeInterval(self.start - datetime.timedelta(seconds=1), self.start)]
                                   + intervals
                                   + [DatetimeInterval(self.end, self.end + datetime.timedelta(seconds=1))])
        simplified_intervals = DatetimeInterval.simplify(intervals_with_boundary)
        whitespace = [DatetimeInterval(interval_before.end, interval_after.start) for interval_before, interval_after
                      in zip(simplified_intervals[:-1], simplified_intervals[1:])]
        return [interval for interval in map(self.intersect, whitespace) if interval]
