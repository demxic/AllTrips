"""This module holds all needed classes"""
from datetime import datetime, timedelta
from models.timeclasses import Duration


class Airport(object):
    """Create airports using the Flyweight pattern
    Try using the weakref.WeakValueDictionary() if  garbage-collection concerned
    for our simple app, not needed
    """
    _airports = dict()

    def __new__(cls, iata_code: str = None, zone=None, viaticum=None):
        airport = cls._airports.get(iata_code)
        if not airport:
            airport = super().__new__(cls)
            cls._airports[iata_code] = airport

        return airport

    def __init__(self, iata_code: str, zone=None, viaticum: str = None):
        """
        Represents an airport as a 3 letter code
        """
        self.iata_code = iata_code
        self.timezone = zone
        self.viaticum = viaticum

    def __str__(self):
        return "{}".format(self.iata_code)


class Itinerary(object):
    """ An Itinerary represents a Duration occurring between a 'begin' and an 'end' datetime.

    begin and end datetimes should be time zone aware. Although, python's duck typing feature
    allows for naive datetimes as well"""

    def __init__(self, begin: datetime, end: datetime):
        """Enter beginning and ending aware-datetime

        In order to facilitate object retrieval and storing, datetime objects are expected to be timezone aware
        and in the UTC format
        """
        self.begin = begin
        self.end = end

    @classmethod
    def from_timedelta(cls, begin: datetime, a_timedelta: timedelta):
        """Returns an Itinerary from a given begin datetime and the timedelta duration of it

        The created Itinerary's end field will have the same timezone as its begin field"""
        end = begin + a_timedelta
        return cls(begin, end)

    @property
    def duration(self) -> Duration:
        return Duration.from_timedelta(self.end - self.begin)

    def astimezone(self, begin_timezone, end_timezone):
        """Returns a new Itinerary instance located in the provided timezone"""
        begin = self.begin.astimezone(begin_timezone)
        end = self.end.astimezone(end_timezone)
        return Itinerary(begin=begin, end=end)

    def __str__(self):
        template = "{0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        return template.format(self)

    def __eq__(self, other):
        return (self.begin == other.begin) and (self.end == other.end)
