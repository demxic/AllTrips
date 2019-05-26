"""This module contains functions that turn each dictionary into an object"""
import datetime

from AdminApp.exceptions import TripBlockError, UnbuiltTripError, DutyDayBlockError, UndefinedBlockTime, \
    PreviouslyStoredTrip, UnsavedRoute, UnstoredTrip
from models.scheduleclasses import Equipment, Route, Airport, Itinerary, Flight, DutyDay, Trip, Airline
from models.timeclasses import DateTimeTracker
import pytz


def get_carrier_code(flight_dict: dict) -> str:
    carrier_code = 'AM'
    if flight_dict['equipment'].startswith(('D', 'E')):
        carrier_code = '6D'
    return carrier_code


def build_itinerary(dt_tracker: DateTimeTracker, flight_dict: dict, suggested_blk: str) -> Itinerary:
    begin = dt_tracker.dt
    if flight_dict['blk'] != '0000':
        # Found a regular flight, create it
        td = dt_tracker.move(flight_dict['blk'])
    elif suggested_blk != '0000' and suggested_blk.isnumeric():
        # Found a DH flight in a duty day with a suggested block time
        td = dt_tracker.move(suggested_blk)
    else:
        # Unable to determine the Itinerary's duration, set it to 0
        td = dt_tracker.move('00:00')
    return Itinerary.from_timedelta(begin=begin, a_timedelta=td)


def build_flight(dt_tracker: DateTimeTracker, flight_dict: dict, postpone: bool, suggested_blk: str) -> Flight:
    # # 1. Get required parameters
    origin = Airport.load_from_db(iata_code=flight_dict['origin'])
    destination = Airport.load_from_db(iata_code=flight_dict['destination'])
    try:
        route = Route.load_from_db(flight_dict['name'][-4:], origin, destination)
    except UnsavedRoute as e:
        print("Route {} not saved in the database".format(e.route))
        ans = input("Want to save it Y/N ?").capitalize()
        if ans == 'Y':
            e.route.save_to_db()
            route = e.route
        else:
            raise e

    carrier_code = get_carrier_code(flight_dict=flight_dict)
    equipment = Equipment.load_from_db(airplane_code=flight_dict['equipment'])
    itinerary = build_itinerary(dt_tracker=dt_tracker, flight_dict=flight_dict, suggested_blk=suggested_blk)

    # 1. Try loading the flight from the database
    loaded_flights = Flight.fetch_all_matching(airline_iata_code=carrier_code,
                                               scheduled_begin=itinerary._begin,
                                               route=route)
    flight = Flight(route=route, scheduled_itinerary=itinerary, equipment=equipment, carrier=carrier_code)

    for loaded_flight in loaded_flights:
        loaded_flight.astimezone(timezone='local')
        flight.astimezone(timezone='local')
        if loaded_flight == flight:
            flight.event_id = loaded_flight.event_id
        elif flight.begin.date() == loaded_flight.begin.date():
            print("¿Cuál es el vuelo correcto?")
            print("1 loaded  flight: ", loaded_flight)
            print("2 created flight: ", flight)
            print("3 ninguno ")
            ans = input('¿1, 2 ó 3? : ')
            if ans == '1':
                flight = loaded_flight
                flight.astimezone(timezone=pytz.utc)
                dt_tracker.dt = flight.end
                break
            elif ans == '2':
                flight.astimezone(timezone=pytz.utc)
                flight.save_to_db()
                break
        elif flight.duration.minutes == 0:
            raise UndefinedBlockTime("No se ha podido deteriminar el blk time del vuelo {}/{}".format(
                flight.name, flight.begin), flight_dict, flight)

    flight.dh = not flight_dict['name'].isnumeric()
    return flight
    # if len(loaded_flights) >1:
    #     for loaded_flight in loaded_flights:
    #         if loaded_flight == flight:
    #             flight = loaded_flight
    # elif len(loaded_flights) == 1:
    #     loaded_flight: Flight = loaded_flights[0]
    #     if flight != loaded_flight:
    #         # TODO : comparar en tiempo local el vuelo cargado con el creado para no tener que preguntar
    #         # TODO : si el vuelo correcto es el vuelo creado, entonces hay que actualizar el vuelo cargado
    #         loaded_flight.astimezone(timezone='local')
    #         flight.astimezone(timezone='local')
    #         print("¿Cuál es el vuelo correcto?")
    #         print("1 loaded  flight: ", loaded_flight)
    #         print("2 created flight: ", flight)
    #         ans = input('¿1 o 2? : ')
    #         flight.astimezone(timezone=pytz.utc)
    #         loaded_flight.astimezone(timezone=pytz.utc)
    #         if ans == '1':
    #             flight = loaded_flight
    #         flight.save_to_db()
    #     else:
    #         flight = loaded_flight
    # elif flight.duration.minutes == 0:
    #         raise UndefinedBlockTime("No se ha podido deteriminar el blk time del vuelo {}/{}".format(
    #         flight.name, flight.begin), flight_dict, flight)
    # else:
    #     flight.save_to_db()
    #
    # flight.dh = not flight_dict['name'].isnumeric()
    # return flight

    # 3. Create and store flight if not found in the DB
    # if not flight:
    #     try:
    #         if flight_dict['blk'] != '0000':
    #             # 4.a Found a regular flight, create it
    #             begin = dt_tracker.dt
    #             td = dt_tracker.move(flight_dict['blk'])
    #             itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)
    #         elif suggested_blk != '0000' and suggested_blk.isnumeric():
    #             # 4.b Found a DH flight in a duty day with a suggested block time
    #             begin = dt_tracker.dt
    #             td = dt_tracker.move(suggested_blk)
    #             itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)
    #             if not itinerary.in_same_month():
    #                 # Flight reaches next month and therefore it's block time cannot be determined
    #                 dt_tracker.move('-'+suggested_blk)
    #                 raise UndefinedBlockTime()
    #         else:
    #             raise UndefinedBlockTime()
    #
    #     except UndefinedBlockTime:
    #
    #         # 4.d Unable to determine flight blk, must enter it manually
    #         if postpone:
    #             raise UnbuiltTripError()
    #         else:
    #             print("FLT {} {} {} {} {} {} ".format(dt_tracker.date, flight_dict['name'],
    #                                                   flight_dict['origin'], flight_dict['begin'],
    #                                                   flight_dict['destination'], flight_dict['end']))
    #             print("unable to determine DH time.")
    #             print("")
    #             blk = input("Insert time as HHMM format :")
    #             td = dt_tracker.forward(blk)
    #             itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)
    #
    #     equipment = Equipment.load_from_db(airplane_code=flight_dict['equipment'])
    #     flight = Flight(route=route, scheduled_itinerary=itinerary,
    #                     equipment=equipment, carrier=carrier_code)
    #     flight.save_to_db()
    # else:
    #     dt_tracker.forward(str(flight.duration))


def build_duty_day(dt_tracker: DateTimeTracker, duty_day_dict: dict, postpone: bool) -> DutyDay:
    """Given a duty_day_dict return it as DutyDay object"""
    dt_tracker.move('1:00')
    duty_day = DutyDay()

    for flight_dict in duty_day_dict['flights']:
        try:
            flight = build_flight(dt_tracker=dt_tracker, flight_dict=flight_dict, postpone=postpone,
                                  suggested_blk=duty_day_dict['crd'])
            duty_day.append(flight)
            dt_tracker.move(flight_dict['turn'])
        except UndefinedBlockTime as e:
            if postpone:
                raise UnbuiltTripError()
            else:
                print("FLT {} {} {} {} {} {} ".format(dt_tracker.date, e.flight_dict['name'],
                                                      e.flight_dict['origin'], e.flight_dict['begin'],
                                                      e.flight_dict['destination'], e.flight_dict['end']))
                print("unable to determine DH time.")
                print("")
                blk = input("Insert time as HHMM format :")
                td = dt_tracker.move(blk)
                itinerary = Itinerary.from_timedelta(begin=e.dt_tracker, a_timedelta=td)
    dt_tracker.move(time_string='00:30')
    dt_tracker.move(duty_day_dict['layover_duration'])

    # Assert that duty day was built properly
    if str(duty_day.duration) != duty_day_dict['dy']:
        raise DutyDayBlockError(duty_day_dict, duty_day)

    return duty_day


def build_trip(trip_dict: dict, postpone: bool) -> Trip:
    dt_tracker = DateTimeTracker(trip_dict['date_and_time'], timezone=pytz.timezone('America/Mexico_City'))
    try:
        trip = Trip.load_trip_info(trip_number=trip_dict['number'], dated=dt_tracker.date)
    except UnstoredTrip:
        trip = Trip(number=trip_dict['number'], dated=dt_tracker.date,
                    crew_position=trip_dict['crew_position'],
                    crew_base=Airport.load_from_db(iata_code=trip_dict['crew_base']))
        dt_tracker.change_to_timezone(pytz.utc)

        for json_dd in trip_dict['duty_days']:
            try:
                duty_day = build_duty_day(dt_tracker, json_dd, postpone)
                trip.append(duty_day)

            except DutyDayBlockError as e:
                print("For trip {0} dated {1}, ".format(trip_dict['number'], trip_dict['dated']), end=' ')
                print("found inconsistent duty day : ")
                print("       ", e.duty_day)
                if postpone:
                    e.delete_invalid_flights()
                    raise UnbuiltTripError
                else:
                    print("... Correcting for inconsistent duty day: ")
                    e.correct_invalid_events()
                    print("Corrected duty day")
                    print(e.duty_day)
                    trip.append(e.duty_day)

        if int(str(trip.duration)) != int(trip_dict['tafb'].replace(':', '')):
            print(trip_dict)
            raise TripBlockError(trip_dict['tafb'], trip)

    return trip


def create_trips(trips_as_dict: list, position: str, postpone: bool = True) -> list:
    # 2. Turn each trip_dict into a Trip object
    built_trips_count: int = 0
    unbuilt_trips = list()
    for trip_dict in trips_as_dict:
        # if 'position' not in trip_dict:
        #     trip_dict['position'] = position
        try:
            # if trip_dict['number'] == '5148':
            #     print("found trip {}".format(trip_dict['number']))
            trip = build_trip(trip_dict, postpone)

        except TripBlockError as e:
            # TODO : Granted, there's a trip block error, what actions should be taken to correct it? (missing)
            print("trip {0.number} dated {0.dated} {0.duration}"
                  " does not match expected TAFB {1}".format(e.trip, e.expected_block_time))
            print("Trip {0} dated {1} unsaved!".format(trip_dict['number'], trip_dict['dated']))
            unbuilt_trips.append(trip_dict)

        except UnbuiltTripError:
            print("Trip {0} dated {1} unsaved!".format(trip_dict['number'], trip_dict['dated']))
            unbuilt_trips.append(trip_dict)

        else:
            trip.position = position
            trip.astimezone('local')
            # print(trip)
            trip.astimezone(pytz.utc)
            # print(trip)
            try:
                trip.save_to_db()
                print("Trip {0.number} dated {0.dated} saved!".format(trip))
                built_trips_count += 1
            except PreviouslyStoredTrip:
                print("Trip {0.number} dated {0.dated} was already stored!".format(trip))

    print("{} json trips found ".format(built_trips_count))
    return unbuilt_trips
