import datetime
from parameterized import parameterized
from productivity.datetime_interval import DatetimeInterval
import unittest

TIMES = [datetime.datetime(2000, 1, day) for day in range(1, 10)]


class TestDatetimeInterval(unittest.TestCase):
    def test_init_value_error(self):
        with self.assertRaises(ValueError):
            DatetimeInterval(start=TIMES[1], end=TIMES[0])

    def test_eq_value_error(self):
        with self.assertRaises(ValueError):
            DatetimeInterval(start=TIMES[0], end=TIMES[1]) == []

    @parameterized.expand([('less', DatetimeInterval(start=TIMES[0], end=TIMES[3]), True),
                           ('equal', DatetimeInterval(start=TIMES[1], end=TIMES[3]), False),
                           ('greater', DatetimeInterval(start=TIMES[2], end=TIMES[3]), False)])
    def test_lt(self, _, interval, desired_result):
        self.assertEqual(desired_result, interval < DatetimeInterval(start=TIMES[1], end=TIMES[3]))

    def test_lt_value_error(self):
        with self.assertRaises(ValueError):
            DatetimeInterval(start=TIMES[0], end=TIMES[1]) < []

    @parameterized.expand([('not_overlapping',
                            DatetimeInterval(TIMES[0], TIMES[1]),
                            DatetimeInterval(TIMES[2], TIMES[3]),
                            None),
                           ('bordering',
                            DatetimeInterval(TIMES[0], TIMES[1]),
                            DatetimeInterval(TIMES[1], TIMES[2]),
                            None),
                           ('fully_overlapping',
                            DatetimeInterval(TIMES[0], TIMES[1]),
                            DatetimeInterval(TIMES[0], TIMES[1]),
                            DatetimeInterval(TIMES[0], TIMES[1])),
                           ('partially_overlapping',
                            DatetimeInterval(TIMES[0], TIMES[2]),
                            DatetimeInterval(TIMES[1], TIMES[3]),
                            DatetimeInterval(TIMES[1], TIMES[2]))
                           ])
    def test_intersect(self, _, interval, other_interval, desired_result):
        self.assertEqual(desired_result, interval.intersect(other_interval))

    @parameterized.expand([('not_overlapping',
                            DatetimeInterval(TIMES[0], TIMES[1]),
                            DatetimeInterval(TIMES[2], TIMES[3]),
                            [DatetimeInterval(TIMES[0], TIMES[1]), DatetimeInterval(TIMES[2], TIMES[3])]),
                           ('bordering',
                            DatetimeInterval(TIMES[0], TIMES[1]),
                            DatetimeInterval(TIMES[1], TIMES[2]),
                            [DatetimeInterval(TIMES[0], TIMES[2])]),
                           ('fully_overlapping',
                            DatetimeInterval(TIMES[0], TIMES[1]),
                            DatetimeInterval(TIMES[0], TIMES[1]),
                            [DatetimeInterval(TIMES[0], TIMES[1])]),
                           ('partially_overlapping',
                            DatetimeInterval(TIMES[0], TIMES[2]),
                            DatetimeInterval(TIMES[1], TIMES[3]),
                            [DatetimeInterval(TIMES[0], TIMES[3])])
                           ])
    def test_union(self, _, interval, other_interval, desired_result):
        self.assertEqual(desired_result, interval.union(other_interval))

    def test_to_minutes(self):
        self.assertEqual(60 * 24, DatetimeInterval(TIMES[0], TIMES[1]).minutes())

    def test_simplify_complex_case(self):
        overlapping_intervals = [DatetimeInterval(TIMES[5], TIMES[7]),  # this list is not ordered
                                 DatetimeInterval(TIMES[6], TIMES[8]),  # overlap with the previous
                                 DatetimeInterval(TIMES[5], TIMES[8]),  # overlap with previous
                                 DatetimeInterval(TIMES[0], TIMES[1]),  # unique interval
                                 DatetimeInterval(TIMES[2], TIMES[3]),
                                 DatetimeInterval(TIMES[3], TIMES[4])]  # this interval borders the previous

        desired_result = [DatetimeInterval(TIMES[0], TIMES[1]),  # unique interval
                          DatetimeInterval(TIMES[2], TIMES[4]),  # comes from 2 bordering intervals
                          DatetimeInterval(TIMES[5], TIMES[8])]  # comes from the 3 overlapping intervals

        self.assertEqual(desired_result, DatetimeInterval.simplify(overlapping_intervals))

    @parameterized.expand([('empty_list', [], []),
                           ('single_item_in_list',
                            [DatetimeInterval(TIMES[0], TIMES[1])],
                            [DatetimeInterval(TIMES[0], TIMES[1])]),
                           ('two_items_in_list',
                            [DatetimeInterval(TIMES[0], TIMES[1]), DatetimeInterval(TIMES[1], TIMES[2])],
                            [DatetimeInterval(TIMES[0], TIMES[2])])
                           ])
    def test_simplify(self, _, intervals, desired_result):
        self.assertEqual(desired_result, DatetimeInterval.simplify(intervals))

    @parameterized.expand([('three_intervals_inside',
                            [DatetimeInterval(TIMES[0], TIMES[1]), DatetimeInterval(TIMES[2], TIMES[3]),
                             DatetimeInterval(TIMES[4], TIMES[5]), DatetimeInterval(TIMES[6], TIMES[7])],
                            [DatetimeInterval(TIMES[1], TIMES[2]), DatetimeInterval(TIMES[3], TIMES[4]),
                             DatetimeInterval(TIMES[5], TIMES[6])]),
                           ('two_intervals_inside',
                            [DatetimeInterval(TIMES[1], TIMES[2]), DatetimeInterval(TIMES[3], TIMES[4]),
                             DatetimeInterval(TIMES[5], TIMES[6]), DatetimeInterval(TIMES[7], TIMES[8])],
                            [DatetimeInterval(TIMES[2], TIMES[3]), DatetimeInterval(TIMES[4], TIMES[5])])
                           ])
    def test_subtract(self, _, intervals, desired_result):
        self.assertEqual(desired_result, DatetimeInterval(TIMES[1], TIMES[6]).subtract(intervals))


if __name__ == '__main__':
    unittest.main()
