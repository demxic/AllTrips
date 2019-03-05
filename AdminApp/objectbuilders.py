"""This module contains functions that turn each dictionary into an object"""
from AdminApp.exceptions import TripBlockError, UnbuiltTripError, DutyDayBlockError, UndefinedBlockTime
from models.timeclasses import DateTimeTracker


def get_carrier(flight_dict):
    carrier_code = 'AM'
    code = flight_dict['name'][0:2]
    if code.startswith('DH'):
        # Found an AM or 6D flight
        if flight_dict['equipment'] == 'DHD':
            carrier_code = '6D'
    elif not code.isdigit():
        # Found a new airline
        carrier_code = code
    return carrier_code


def get_route(name: str, origin: Airport, destination: Airport) -> Route:
    route_key = name + origin.iata_code + destination.iata_code
    if route_key not in Route._routes:
        # Route has not been loaded from the DB
        route = Route.load_from_db_by_fields(name=name,
                                             origin=origin,
                                             destination=destination)
        if not route:
            # Route must be created and stored into DB
            route = Route(name=name, origin=origin, destination=destination)
            route.save_to_db()
    else:
        route = Route._routes[route_key]
    return route


def get_flight(dt_tracker: DateTimeTracker, flight_dict: dict,
               postpone: bool, suggested_blk: str) -> Flight:
    # 1. Get the route
    # take into consideration the last 4 digits Because some flights start with 'DH'
    # origin = get_airport(flight_dict['origin'])
    # destination = get_airport(flight_dict['destination'])
    # origin = Airport(flight_dict['origin'])
    # destination = Airport(flight_dict['destination'])
    origin = flight_dict['origin']
    destination =flight_dict['destination']
    route = get_route(flight_dict['name'][-4:], origin, destination)

    # 2. We need the airline code
    carrier_code = get_carrier(flight_dict)

    # 3. Find the flight in the DB
    begin = copy(dt_tracker.dt)
    flight = Flight.load_from_db_by_fields(airline_iata_code=carrier_code,
                                           scheduled_begin=begin,
                                           route=route)

    # 4. Create and store flight if not found in the DB
    if not flight:
        try:
            if flight_dict['blk'] != '0000':
                # 4.a Found a regular flight, create it
                td = dt_tracker.forward(flight_dict['blk'])
                itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)
            elif suggested_blk != '0000' and suggested_blk.isnumeric():
                # 4.b Found a DH flight in a duty day with a suggested block time
                td = dt_tracker.forward(suggested_blk)
                itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)
                if not itinerary.in_same_month():
                    # Flight reaches next month and therefore it's block time cannot be determined
                    dt_tracker.backward(suggested_blk)
                    raise UndefinedBlockTime()
            else:
                raise UndefinedBlockTime()

        except UndefinedBlockTime:

            # 4.d Unable to determine flight blk, must enter it manually
            if postpone:
                raise UnbuiltTripError()
            else:
                print("FLT {} {} {} {} {} {} ".format(dt_tracker.date, flight_dict['name'],
                                                      flight_dict['origin'], flight_dict['begin'],
                                                      flight_dict['destination'], flight_dict['end']))
                print("unable to determine DH time.")
                print("")
                blk = input("Insert time as HHMM format :")
                td = dt_tracker.forward(blk)
                itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)

        equipment = Equipment(flight_dict['equipment'])
        flight = Flight(route=route, scheduled_itinerary=itinerary,
                        equipment=equipment, carrier=carrier_code)
        flight.save_to_db()
    else:
        dt_tracker.forward(str(flight.duration))

    flight.dh = not flight_dict['name'].isnumeric()
    return flight


def get_duty_day(dt_tracker, duty_day_dict, postpone):
    """Given a duty_day_dict return it as DutyDay object"""
    dt_tracker.start()
    duty_day = DutyDay()

    for flight_dict in duty_day_dict['flights']:
        flight = get_flight(dt_tracker, flight_dict, postpone, suggested_blk=duty_day_dict['crd'])
        if flight:
            duty_day.append(flight)
            dt_tracker.forward(flight_dict['turn'])
    dt_tracker.release()
    dt_tracker.forward(duty_day_dict['layover_duration'])

    # Assert that duty day was built properly
    if str(duty_day.duration) != duty_day_dict['dy']:
        raise DutyDayBlockError(duty_day_dict, duty_day)

    return duty_day


def build_trip(trip_dict: dict, postpone: bool) -> Trip:
    dt_tracker = DateTimeTracker(trip_dict['date_and_time'])
    trip = Trip(number=trip_dict['number'], dated=dt_tracker.date)

    for json_dd in trip_dict['duty_days']:
        try:
            duty_day = get_duty_day(dt_tracker, json_dd, postpone)
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

    return trip


def create_trips(trips_as_dict, position, postpone=True) -> list:
    # 2. Turn each trip_dict into a Trip object
    built_trips_count: int = 0
    unbuilt_trips = list()
    for trip_dict in trips_as_dict:
        if 'position' not in trip_dict:
            trip_dict['position'] = position
        built_trips_count += 1
        try:
            # if trip_dict['number'] == '3760':
            #     input("Enter para continuar")
            trip = build_trip(trip_dict, postpone)
            if trip.duration.no_trailing_zero() != trip_dict['tafb']:
                print(trip_dict)
                raise TripBlockError(trip_dict['tafb'], trip)

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
            print("Trip {0.number} dated {0.dated} saved".format(trip))
            trip.position = position
            trip.save_to_db()

    print("{} json trips found ".format(built_trips_count))
    return unbuilt_trips
