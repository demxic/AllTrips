"""This module holds functions needed to read pbs.txt files and turn them into schedule classes"""
from typing import Dict, List
from AdminApp.adminregex import page_number_RE, trips_total_RE, trip_RE, dutyday_RE, flights_RE


def verify_files(data_folder: str, file_names: list) -> list:
    """
    Verify files existence in data_folder

    """
    files = list()
    for file_name in file_names:
        file_to_be_read = data_folder / file_name
        if file_to_be_read.is_file():
            print("file {} found".format(file_name))
            files.append(file_to_be_read)
        else:
            print("file {} not found!".format(file_name))
    return files


def page_number_remover(file: str) -> str:
    """
    Remove =======pagenumber======= string from trips.txt file

    When using PDF Mate converter tu turn each .pdf file into .txt, the app will insert
    such long string with page numbers. This must be removed in order to read all trips
    correctly

    """
    with open(file, 'r') as f:
        content = f.read()
        content_new = page_number_RE.sub(repl='', string=content)
    return content_new


def number_of_trips_in_pbs_file(pbs_file_content: str) -> int:
    """Searches for the 'Total number of trips' inside the pbs_file_content and returns the total number """
    match_obj = trips_total_RE.search(pbs_file_content)
    total_trips = int(match_obj.groupdict()['trips_total'])
    return total_trips


def create_trips_as_dict(trips_as_strings: str, crew_position: str, trip_base: str) -> list:
    """Return a list containing all trip_as_dict from its corresponding trip_string"""

    dict_trips = []
    for trip_match in trip_RE.finditer(trips_as_strings):
        trip_as_dict = get_trip_as_dict(trip_match.groupdict())
        trip_as_dict['crew_position'] = crew_position
        trip_as_dict['trip_base'] = trip_base
        dict_trips.append(trip_as_dict)
        print("Trip {} dated {} found!".format(trip_as_dict['number'], trip_as_dict['dated']))

    return dict_trips


def get_trip_as_dict(trip_dict: dict) -> dict:
    """
    Given a dictionary containing PBS trip data, turn it into a dictionary

    """
    trip_dict['date_and_time'] = trip_dict['dated'] + trip_dict['check_in']
    dds = list()

    for duty_day_match in dutyday_RE.finditer(trip_dict['duty_days']):
        duty_day = get_dutyday_as_dict(duty_day_match.groupdict())
        dds.append(duty_day)
    trip_dict['duty_days'] = dds

    return trip_dict


def get_dutyday_as_dict(duty_day_dict: dict) -> dict:
    """
    Given a dictionary containing pbs duty_day data, do some needed formatting
    """

    duty_day_dict['layover_duration'] = duty_day_dict['layover_duration'] if duty_day_dict[
        'layover_duration'] else '0000'

    # The last flight in a duty_day must be re-arranged
    dictionary_flights: List[Dict[str, str]] = [f.groupdict() for f in flights_RE.finditer(duty_day_dict['flights'])]
    duty_day_dict['rls'] = dictionary_flights[-1]['blk']
    dictionary_flights[-1]['blk'] = dictionary_flights[-1]['turn']
    dictionary_flights[-1]['turn'] = '0000'

    duty_day_dict['flights'] = dictionary_flights

    return duty_day_dict
