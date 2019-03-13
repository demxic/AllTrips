from unittest import TestCase
from models.timeclasses import Duration
from datetime import timedelta


class TestDuration(TestCase):
    def setUp(self):
        self.duration = Duration(minutes=40)
        self.td = timedelta(minutes=40)


class TestInit(TestDuration):
    def test_initial_minutes(self):
        self.assertEqual(self.duration.minutes, 40)

    def test_from_timedelta(self):
        duration = Duration.from_timedelta(self.td)
        self.assertEqual(self.duration, duration)

    def test_from_string(self):
        duration = Duration.from_string('0040')
        self.assertEqual(duration, self.duration)


class TestAsTimeDelta(TestDuration):
    def test_from_minutes(self):
        td = self.duration.as_timedelta()
        self.assertEqual(td, self.td)


class TestNoTrailingZero(TestDuration):
    def test_from_zero(self):
        result = self.duration.no_trailing_zero()
        self.assertEqual('0:40', result)
