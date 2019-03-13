from datetime import datetime, timedelta

from models.modelsregex import duration_fmt


class Duration(object):
    default_format = '<4'

    def __init__(self, minutes: int):
        """value should be minutes (int)"""
        if minutes < 0:
            minutes = 0
        self.minutes = int(minutes)

    @classmethod
    def from_timedelta(cls, td: timedelta):
        minutes = int(td.total_seconds() / 60)
        return cls(minutes)

    @classmethod
    def from_string(cls, value: str):
        """string value should not have ':'"""
        hours = int(value[0:-2])
        minutes = int(value[-2:])
        return cls(minutes=hours * 60 + minutes)

    def get_hours_and_minutes(self):
        """Returns the total number of hours and minutes in the duration as a tuple"""
        return divmod(self.minutes, 60)

    def as_timedelta(self):
        return timedelta(minutes=self.minutes)

    def __add__(self, other):
        return Duration(self.minutes + other.minutes)

    def __radd__(self, other):
        """Because sum(x) always starts adding a 0, Duration takes this into account in this method"""
        return Duration(self.minutes + other.minutes)

    def __sub__(self, other):
        return Duration(self.minutes - other.minutes)

    def __rsub__(self, other):
        return Duration(self.minutes - other.minutes)

    def __mul__(self, other):
        return self.minutes / 60 * other

    def __rmul__(self, other):
        return self.__mul__(other)

    def __lt__(self, other):
        return self.minutes < other.minutes

    def __eq__(self, other):
        return self.minutes == other.minutes

    def __str__(self):
        """Prints as HHMM v.gr. 1230"""
        return self.__format__(Duration.default_format)

    def __repr__(self):
        return "{__class__.__name__}({minutes})".format(__class__=self.__class__, **self.__dict__)

    def __format__(self, format_spec):
        """Depending on format_spec value, a Duration can be printed as follow:

        [[fill]align][minimumwidth][:][visibility]
        fill : character to be used to pad the field to the minimum width
        align : '<' - Forces the field to be left-aligned within the available space (This is the default.)
                '>' - Forces the field to be right-aligned within the available space.
        :       include the colon when it should be printed out
        visibility  :  Show or hide durations of 0 minutes.
                        "T" - Show 00:00 or 0000 durations (This is the default.)
                        "F" - Show '    ' instead.
        """

        if format_spec == "":
            format_spec = self.default_format
        rs = duration_fmt.match(format_spec).groupdict()
        if rs['hide_if_zero']:
            basic_string = ' '
        else:
            rs['fill_align'] = rs['fill_align'] if rs['fill_align'] else ''
            rs['size'] = rs['size'] if rs['size'] else ''
            rs['colon'] = rs['colon'] if rs['colon'] else ''
            basic_string = "{0}{2}{1}".format(*self.get_hours_and_minutes(), rs['colon'])
        result = "{0:{fill_align}{size}s}".format(basic_string, **rs)
        return result


class DateTimeTracker(object):
    """Used to keep track of a dt object in order to build Itineraries"""

    def __init__(self, begin: str):
        self.datetime_format = "%d%b%Y%H:%M"
        self.dt = datetime.strptime(begin, self.datetime_format)

    def start(self):
        """Moves one hour ahead"""
        self.dt += timedelta(hours=1)

    def release(self):
        """Moves half an hour ahead"""
        self.dt += timedelta(minutes=30)

    def forward(self, time_string: str) -> timedelta:
        """Moves HH hours and MM minutes forward in time.
        time_string may be of type HH:MM or HHMM
        """
        hh = int(time_string[:2])
        mm = int(time_string[-2:])
        td: timedelta = timedelta(hours=hh, minutes=mm)
        self.dt += td
        return td

    def backward(self, time_string: str) -> timedelta:
        """Moves HH hours and MM minutes backward in time.
        time_string may be of type HH:MM or HHMM
        """
        hh = int(time_string[:2])
        mm = int(time_string[-2:])
        td: timedelta = timedelta(hours=hh, minutes=mm)
        self.dt -= td
        return td

    @property
    def date(self):
        return self.dt.date()

    def __str__(self):
        return self.dt.strftime(self.datetime_format)
