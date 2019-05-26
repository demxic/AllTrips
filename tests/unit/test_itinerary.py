import pytest
import json

from models.scheduleclasses import Itinerary
from tests.json_loader import object_decode

airports_file = "C://Users//Xico//Documents//PycharmProjects//AllTrips//tests//fixtures//airports.json"
itineraries_file = "C://Users//Xico//Documents//PycharmProjects//AllTrips//tests//fixtures//itineraries.json"


def json_loader(filename):
    """Loads data from JSON file"""

    with open(filename, "r", encoding="UTF-8") as source:
        data = json.load(source, object_hook=object_decode)
    return data


itineraries = json_loader(itineraries_file)


@pytest.mark.parametrize('itinerary_dict', itineraries, ids=[str(index) for index in range(0, len(itineraries))])
def test_itinerary_init(itinerary_dict):
    itinerary = Itinerary(**itinerary_dict)
    assert itinerary.begin == itinerary_dict['begin']
    assert itinerary.end == itinerary_dict['end']


@pytest.mark.parametrize('itinerary_dict', itineraries, ids=[str(index) for index in range(0, len(itineraries))])
def test_as_timezone(itinerary_dict):
    itinerary = Itinerary(**itinerary_dict)
    assert itinerary.begin == itinerary_dict['begin']
    assert itinerary.end == itinerary_dict['end']
# class TestAwareItinerary(TestCase):
#     def setUp(self):
#         # format example: 13081979 0830
#         self.date_format = "%d%m%Y"
#         self.time_format = "%H%M"
#         self.datetime_format = self.date_format + ' ' + self.time_format
#         self.mex_tz = pytz.timezone('America/Mexico_City')
#         self.mad_tz = pytz.timezone('Europe/Madrid')
#
#         # UNAWARE objects, itinerary for flight AM0001/01FEB2019   MEX 0100 MAD 1130  (UTC times)
#         #
#         self.begin_unaware = datetime.strptime("01022019 0100", self.datetime_format)
#         self.end_unaware = datetime.strptime("01022019 1130", self.datetime_format)
#         self.itinerary_unaware = Itinerary(begin=self.begin_unaware, end=self.end_unaware)
#         self.duration_as_timedelta = self.end_unaware - self.begin_unaware
#
#         #   AWARE objects, itinerary for flight AM0001/31JAN2019   MEX 1900 MAD 1230  (local times)
#         #                                              31JAN2019   MEX 1900 MAD 0430  (MEX times)
#         #                                              01FEB2019   MEX 0200 MAD 1230  (MAD times)
#         #                                              01FEB2019   MEX 0100 MAD 1130  (UTC times)
#         self.begin_aware = pytz.utc.localize(self.begin_unaware)
#         self.end_aware = pytz.utc.localize(self.end_unaware)
#         self.duration = Duration.from_timedelta(self.end_aware - self.begin_aware)
#         self.itinerary_aware = Itinerary(begin=self.begin_aware, end=self.end_aware)
#
#
# class TestAwareInit(TestAwareItinerary):
#     def test_from_timedelta(self):
#         itinerary = Itinerary.from_timedelta(begin=self.begin_aware, a_timedelta=self.duration_as_timedelta)
#         self.assertEqual(self.duration, itinerary.duration)
#
#
# class TestAsTimeZone(TestAwareItinerary):
#     def test_as_MEX_time_zone(self):
#         begin_as_mex_timezone = self.begin_aware.astimezone(self.mex_tz)
#         end_as_mex_timezone = self.end_aware.astimezone(self.mex_tz)
#         itinerary_as_mex_time_zone = self.itinerary_aware.astimezone(begin_timezone=self.mex_tz,
#                                                                      end_timezone=self.mex_tz)
#         self.assertEqual(begin_as_mex_timezone, itinerary_as_mex_time_zone.begin)
#         self.assertEqual(end_as_mex_timezone, itinerary_as_mex_time_zone.end)
#
#     def test_as_MAD_time_zone(self):
#         begin_as_mad_timezone = self.begin_aware.astimezone(self.mad_tz)
#         end_as_mad_timezone = self.end_aware.astimezone(self.mad_tz)
#         itinerary_as_mad_time_zone = self.itinerary_aware.astimezone(begin_timezone=self.mad_tz,
#                                                                      end_timezone=self.mad_tz)
#         self.assertEqual(begin_as_mad_timezone, itinerary_as_mad_time_zone.begin)
#         self.assertEqual(end_as_mad_timezone, itinerary_as_mad_time_zone.end)
#
#     def test_as_mixed_time_zones(self):
#         """Also known as local time zone"""
#         begin_as_mex_timezone = self.begin_aware.astimezone(self.mex_tz)
#         end_as_mad_timezone = self.end_aware.astimezone(self.mad_tz)
#         itinerary_as_mixed_time_zones = self.itinerary_aware.astimezone(begin_timezone=self.mex_tz,
#                                                                         end_timezone=self.mad_tz)
#         self.assertEqual(begin_as_mex_timezone, itinerary_as_mixed_time_zones.begin)
#         self.assertEqual(end_as_mad_timezone, itinerary_as_mixed_time_zones.end)
#
#
# class TestPrint(TestAwareItinerary):
#     def test_print_as_mex_timezone(self):
#         expected = "31Jan BEGIN 1900 END 0530"
#         itinerary_as_mex_time_zone = self.itinerary_aware.astimezone(begin_timezone=self.mex_tz,
#                                                                      end_timezone=self.mex_tz)
#         self.assertEqual(expected, itinerary_as_mex_time_zone.__str__())
#
#     def test_print_as_mad_timezone(self):
#         expected = "01Feb BEGIN 0200 END 1230"
#         itinerary_as_mad_time_zone = self.itinerary_aware.astimezone(begin_timezone=self.mad_tz,
#                                                                      end_timezone=self.mad_tz)
#         self.assertEqual(expected, itinerary_as_mad_time_zone.__str__())
#
#     def test_print_as_mixed_timezones(self):
#         expected = "31Jan BEGIN 1900 END 1230"
#         itinerary_as_mixed_time_zones = self.itinerary_aware.astimezone(begin_timezone=self.mex_tz,
#                                                                         end_timezone=self.mad_tz)
#         self.assertEqual(expected, itinerary_as_mixed_time_zones.__str__())
