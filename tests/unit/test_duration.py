from datetime import timedelta

import pytest

from models.timeclasses import Duration


class TestInitMethods:

    @pytest.fixture(scope='module', params=[30, 235, 23*60+30])
    def minutes(self, request):
        minutes = request.param
        yield minutes

    def test_init(self, minutes):
        duration = Duration(minutes)
        assert isinstance(duration, Duration)
        assert duration.minutes == minutes


class TestFormattingMethods:

    def test_duration_formatting_default(self):
        d = Duration(23 * 60 + 30)
        expected = "23:30"
        obtained = "{0:<5:}".format(d)
        assert expected == obtained

    def test_duration_formatting_no_colon(self):
        d = Duration(23 * 60 + 30)
        expected = "2330"
        obtained = "{0:<4}".format(d)
        assert expected == obtained

    def test_duration_formatting_zero_show(self):
        d = Duration(0)
        expected = '0000'
        obtained = "{0:0<4}".format(d)
        assert obtained == expected

    def test_duration_formatting_zero_hide(self):
        d = Duration(0)
        expected = 4 * ' '
        obtained = "{0:<4H}".format(d)
        assert obtained == expected

    def test_duration_rep_method(self):
        d = Duration(23 * 60 + 30)
        expected = "Duration({})".format(23 * 60 + 30)
        obtained = d.__repr__()
        assert obtained == expected


def test_as_timedelta():
    td = timedelta(minutes=30)
    d = Duration.from_timedelta(td)
    assert isinstance(d, Duration)
    assert td.total_seconds() == 30*60


