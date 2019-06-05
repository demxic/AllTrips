"""This module holds all needed classes"""
from datetime import datetime, timedelta, date
import pytz
from AdminApp.exceptions import UnsavedRoute, PreviouslyStoredTrip, UnstoredTrip
from data.database import CursorFromConnectionPool
from models.timeclasses import Duration



class Airline(object):
    _airlines = dict()

    def __new__(cls, airline_code, airline_name):
        airline = cls._airlines.get(airline_code)
        if not airline:
            airline = super().__new__(cls)
            cls._airlines[airline_code] = airline
        return airline

    def __init__(self, airline_code: str, airline_name: str = "Aeroméxico"):
        if not hasattr(self, 'initted'):
            self.airline_code = airline_code
            self.airline_name = airline_name
            self.initted = True

    @classmethod
    def load_from_db(cls, airline_code: str):
        airline = cls._airlines.get(airline_code.upper())
        if not airline:
            with CursorFromConnectionPool() as cursor:
                cursor.execute('SELECT * FROM airlines WHERE iata_code=%s;', (airline_code,))
                airline_data = cursor.fetchone()
                airline = cls(airline_code=airline_data[0], airline_name=airline_data[1])
        return airline

    def __str__(self):
        return self.airline_code if self.airline_code else 2 * ' '

    def __repr__(self):
        return "<{__class__.__name__}> {airline_code}".format(__class__=self.__class__, **self.__dict__)


class Airport(object):
    """Create airports using the Flyweight pattern
    Try using the weakref.WeakValueDictionary() if  garbage-collection concerned
    for our simple app, not needed
    """
    _airports = dict()

    def __new__(cls, iata_code: str = None, timezone=None, viaticum=None):
        airport = cls._airports.get(iata_code)
        if not airport:
            airport = super().__new__(cls)
            cls._airports[iata_code] = airport

        return airport

    def __init__(self, iata_code: str, timezone: pytz.timezone = None, viaticum: str = None) :
        """
        Represents an airport as a 3 letter code
        """
        if not hasattr(self, 'initted'):
            self.iata_code = iata_code
            self.timezone = timezone
            self.viaticum = viaticum
            self.initted = True

    def __str__(self):
        return "{}".format(self.iata_code)

    @classmethod
    def load_from_db(cls, iata_code: str):
        airport = cls._airports.get(iata_code.upper())
        if not airport:
            with CursorFromConnectionPool() as cursor:
                cursor.execute('SELECT * FROM airports WHERE iata_code=%s;', (iata_code,))
                airport_data = cursor.fetchone()
                timezone = pytz.timezone(airport_data[1] + '/' + airport_data[2])
                airport = cls(iata_code=airport_data[0], timezone=timezone, viaticum=airport_data[3])
        return airport

    def __repr__(self):
        return "<{__class__.__name__}> {iata_code}".format(__class__=self.__class__, **self.__dict__)


class CrewMember(object):
    """Defines a CrewMember"""

    def __init__(self, crew_member_id: int = None, name: str = None, pos: str = None, crew_group: str = None,
                 base: Airport = None, seniority: int = None):
        self.crew_member_id = crew_member_id
        self.name = name
        self.position = pos
        self.crew_group = crew_group
        self.base = base
        self.seniority = seniority
        self.line = None

    def __str__(self):
        return "{0:3s} {1:6s}-{2:12s}".format(self.position, self.crew_member_id, self.name)


class Equipment(object):
    _equipments = dict()

    def __new__(cls, airplane_code, cabin_members):
        """Use the flyweight pattern to create only one object """
        equipment = cls._equipments.get(airplane_code)
        if not equipment:
            equipment = super().__new__(cls)
            cls._equipments[airplane_code] = equipment
        return equipment

    def __init__(self, airplane_code, cabin_members: int = 0):
        if not hasattr(self, 'initted'):
            self.airplane_code = airplane_code
            self.cabin_members = cabin_members
            self.initted = True

    def __str__(self):
        return self.airplane_code if self.airplane_code else 3 * ' '

    def __eq__(self, other) -> bool:
        return self.airplane_code == other.airplane_code

    def __repr__(self):
        return "<{__class__.__name__}> {airplane_code}".format(__class__=self.__class__, **self.__dict__)

    @classmethod
    def load_from_db(cls, airplane_code: str):
        equipment = cls._equipments.get(airplane_code.upper())
        if not equipment:
            with CursorFromConnectionPool() as cursor:
                cursor.execute('SELECT * FROM equipments WHERE airplane_code=%s;', (airplane_code,))
                equipment_data = cursor.fetchone()
                equipment = cls(airplane_code=equipment_data[0], cabin_members=equipment_data[1])
        return equipment


class Route(object):
    """For a given airline, represents a flight number or ground duty name
        with its origin and destination airports
        Note: flights and ground duties are called Events"""
    _routes = dict()

    def __new__(cls, name: str, origin: Airport, destination: Airport, route_id: int):
        route_key = name + origin.iata_code + destination.iata_code
        route = cls._routes.get(route_key)
        if not route:
            route = super().__new__(cls)
            cls._routes[route_key] = route
        return route

    def __init__(self, name: str, origin: Airport, destination: Airport, route_id: int = None):
        """Flight numbers have 4 digits only"""
        if not hasattr(self, 'initted'):
            self.route_id = route_id
            self.name = name
            self.origin = origin
            self.destination = destination
            self.initted = True

    @classmethod
    def load_from_db(cls, name: str, origin: Airport, destination: Airport):
        route = cls(name=name, origin=origin, destination=destination, route_id=None)
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT route_id FROM public.routes '
                           '    WHERE name=%s'
                           '      AND origin=%s'
                           '      AND destination=%s',
                           (name, origin.iata_code, destination.iata_code))
            route_id = cursor.fetchone()
            if route_id:
                route.route_id = route_id[0]
                return route
            else:
                raise UnsavedRoute(route=route)

    @classmethod
    def load_by_id(cls, route_id : int):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT name, origin, destination '
                           '    FROM public.routes '
                           '    WHERE route_id=%s',
                           (route_id,))
            route_data = cursor.fetchone()
            origin = Airport.load_from_db(iata_code=route_data[1])
            destination = Airport.load_from_db(iata_code=route_data[2])

            return cls(name=route_data[0], origin=origin,
                       destination=destination, route_id=route_id)

    def save_to_db(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('INSERT INTO public.routes(name, origin, destination) '
                           'VALUES (%s, %s, %s) '
                           'RETURNING route_id; ',
                           (self.name, self.origin.iata_code, self.destination.iata_code))
            route_id = cursor.fetchone()[0]
            self.route_id = route_id
            return route_id

    def __eq__(self, other):
        """Two routes are the same if their parameters are equal"""
        return all((self.name == other.name, self.origin == other.origin, self.destination == other.destination))

    def __str__(self):
        return "{name} {origin} {destination}".format(**self.__dict__)

    def __repr__(self):
        return "<{__class__.__name__}> {name} {origin} {destination}".format(
            __class__=self.__class__, **self.__dict__)


class Itinerary(object):
    """ An Itinerary represents a Duration occurring between a 'begin' and an 'end' datetime.

    begin and end datetimes should be time zone aware. Although, python's duck typing feature
    allows for naive datetimes as well"""

    def __init__(self, begin: datetime, end: datetime):
        """Enter beginning and ending aware-datetime

        In order to facilitate object retrieval and storing, datetime objects are expected to be timezone aware
        and in the UTC format
        """
        self._begin = begin
        self._end = end
        self.begin_timezone_displayed = None
        self.end_timezone_displayed = None

    @property
    def begin(self):
        """Will return begin as an aware datetime object set to begin_timezone"""
        if self.begin_timezone_displayed:
            return self._begin.astimezone(self.begin_timezone_displayed)
        else:
            return self._begin

    @property
    def end(self):
        if self.end_timezone_displayed:
            return self._end.astimezone(self.end_timezone_displayed)
        else:
            return self._end

    @classmethod
    def from_timedelta(cls, begin: datetime, a_timedelta: timedelta):
        """Returns an Itinerary from a given begin datetime and the timedelta duration of it

        The created Itinerary's end field will have the same timezone as its begin field"""
        end = begin + a_timedelta
        return cls(begin, end)

    @classmethod
    def from_date_and_strings(cls, date: datetime.date, begin: str, end: str, timezone=None):
        """date should  be a datetime.date object
        begin and end should have a %H%M (2345) format"""
        begin = '0000' if begin == '2400' else begin
        end = '0000' if end == '2400' else end
        formatting = '%H%M'
        begin_string = datetime.strptime(begin, formatting).time()
        begin = datetime.combine(date, begin_string)
        end_string = datetime.strptime(end, formatting).time()
        end = datetime.combine(date, end_string)

        if end < begin:
            end += timedelta(days=1)
        if timezone:
            # Specify the given timezone
            begin = timezone.localize(begin)
            end = timezone.localize(end)
            # And turn them into utc, as this is how all objects should be created
            begin = begin.astimezone(pytz.utc)
            end = end.astimezone(pytz.utc)
        itinerary = cls(begin=begin, end=end)
        return itinerary

    @property
    def duration(self) -> Duration:
        return Duration.from_timedelta(self.end - self.begin)

    @property
    def _json(self):
        return dict(__class__=self.__class__.__name__,
                    __args__=[],
                    __kw__=dict(begin=self.begin, end=self.end))

    def astimezone(self, begin_timezone, end_timezone):
        """Changes the time zone to be displayed"""
        self.begin_timezone_displayed = begin_timezone
        self.end_timezone_displayed = end_timezone

    def __str__(self):
        template = "{0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        return template.format(self)

    def __eq__(self, other):
        return (self.begin == other.begin) and (self.end == other.end)




class Event(object):
    """
    Represents  Vacations, GDO's, time-off, etc.
    Markers don't account for duty or block time in a given month
    """

    def __init__(self, route: Route, scheduled_itinerary: Itinerary = None, event_id: int = None):
        self.route = route
        self.scheduled_itinerary = scheduled_itinerary
        self.event_id = event_id
        self._credits = None

    @staticmethod
    def create_event_parameters() -> dict:
        """Ask user to input a scheduled itinerary

            scheduled_itinerary = 100813 0823 1345
            actual_itinerary = None

        """
        event_parameters = dict()
        event_parameters['route'] = Route.create_route()
        answer = input("Do you know the scheduled itinerary for this event? Y/N :").capitalize()[0]
        if answer == 'Y':
            event_parameters['scheduled_itinerary'] = Itinerary.create_itinerary()
        else:
            event_parameters['scheduled_itinerary'] = None
        return event_parameters

    @property
    def name(self) -> str:
        """Although an Event is more likely to be localized, using Route
            to store and retrieve information makes for a better class hierarchy"""
        return self.route.name

    @property
    def begin(self) -> datetime:
        return self.scheduled_itinerary.begin if self.scheduled_itinerary else None

    @property
    def end(self) -> datetime:
        return self.scheduled_itinerary.end if self.scheduled_itinerary else None

    @property
    def duration(self) -> Duration:
        return Duration.from_timedelta(self.end - self.begin)

    def compute_credits(self, creditator=None):
        self._credits = {'block': Duration(0), 'dh': Duration(0), 'daily': Duration(0)}

    def astimezone(self, timezone='local'):
        """Change event's itineraries to given timezone"""
        if timezone != 'local':
            self.scheduled_itinerary.astimezone(begin_timezone=timezone,
                                                end_timezone=timezone)
        else:
            self.scheduled_itinerary.astimezone(begin_timezone=self.route.origin.timezone,
                                                end_timezone=self.route.destination.timezone)

    def __str__(self) -> str:
        if self.scheduled_itinerary:
            template = "{0.route.name} {0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        else:
            template = "{0.route.name}"
        return template.format(self)


class GroundDuty(Event):
    """
    Represents  training, reserve or special assignments.
    Ground duties do account for some credits
    """

    def __init__(self, route: Route, scheduled_itinerary: Itinerary = None, position: str = None,
                 equipment=None, event_id: int = None) -> None:
        super().__init__(route=route, scheduled_itinerary=scheduled_itinerary, event_id=event_id)
        self.position = position
        self.equipment = equipment

    @staticmethod
    def create_ground_duty_parameters() -> dict:
        """
        Given an event_dict as a dict, turn it into a Ground Duty object
            ground_duty_string = 100818 E3 MEX 0823 1345

        """
        event_parameters = Event.create_event_parameters()
        event_parameters['position'] = input("Is this an EJE or SOB position? ").capitalize()[:3]
        return event_parameters

    @property
    def report(self) -> datetime:
        return self.begin

    @property
    def release(self) -> datetime:
        return self.end

    def as_robust_string(self, rpt=4 * '', rls=4 * '', turn=4 * ''):
        """Prints a Ground Duty following this heather template
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN       EQ
        05JUN 0900 E6     MEX 0900 MEX 1500 1500 0000

        OR ********************************************************************
        Prints a Flight following this heather template
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN       EQ
        03JUN 1400 0924   MEX 1500 MTY 1640 1720 0140       0000       738


        Following arguments being optional
        rpt : report
        rls : release
        turn: turn around time
        eq : equipment"""

        template = """
        {0.begin:%d%b} {rpt:4s} {0.name:<6s} {0.route.origin} {0.begin:%H%M} {0.route.destination} {0.end:%H%M} {rls:4s} {block}       {turn:4s}       {0.equipment}"""
        self.compute_credits()
        block = self._credits['block']
        return template.format(self, rpt=rpt, rls=rls, turn=turn, block=block)


class Flight(GroundDuty):

    def __init__(self, route: Route, scheduled_itinerary: Itinerary = None, actual_itinerary: Itinerary = None,
                 equipment: Equipment = None, carrier: str = 'AM', event_id: int = None, dh=False, position=None):
        """
        Holds those necessary fields to represent a Flight Itinerary
        """
        super().__init__(route=route, scheduled_itinerary=scheduled_itinerary, equipment=equipment,
                         event_id=event_id, position=position)
        self.actual_itinerary = actual_itinerary
        self.carrier = carrier
        self.dh = dh
        # self.is_flight = True

    @property
    def begin(self) -> datetime:
        return self.actual_itinerary.begin if self.actual_itinerary else self.scheduled_itinerary.begin

    @begin.setter
    def begin(self, new_begin: datetime):
        if self.actual_itinerary:
            self.actual_itinerary.begin = new_begin
        else:
            self.scheduled_itinerary.begin = new_begin

    @property
    def end(self) -> datetime:
        return self.actual_itinerary.end if self.actual_itinerary else self.scheduled_itinerary.end

    @end.setter
    def end(self, new_end: datetime):
        if self.actual_itinerary:
            self.actual_itinerary.end = new_end
        else:
            self.scheduled_itinerary.end = new_end

    @property
    def name(self) -> str:
        """
        Returns the full flight name, composed of a prefix and a flight_number
        prefix indicates a DH flight by AM or any other company
        """
        prefix = ''
        if self.dh:
            if self.carrier == 'AM' or self.carrier == '6D':
                prefix = 'DH'
            else:
                prefix = self.carrier
        return prefix + self.route.name

    @property
    def report(self) -> datetime:
        """Flight's report time"""
        if not self.scheduled_itinerary:
            return self.actual_itinerary.begin - timedelta(hours=1)
        else:
            return self.scheduled_itinerary.begin - timedelta(hours=1)

    @property
    def release(self) -> datetime:
        """Flights's release time """
        if not self.actual_itinerary:
            return self.scheduled_itinerary.end + timedelta(minutes=30)
        else:
            return self.actual_itinerary.end + timedelta(minutes=30)

    def __eq__(self, other):
        """Two flights are said to be equal if the carrier, route, scheduled itinerary and duration are the same"""
        return self.carrier == other.carrier and self.scheduled_itinerary == other.scheduled_itinerary and \
               self.duration == other.duration and self.route == other.route

    def compute_credits(self, creditator=None):
        if self.dh:
            dh = self.duration
            block = Duration(0)
        else:
            block = self.duration
            dh = Duration(0)
        self._credits = {'block': block, 'dh': dh}

    # TODO : Modify to save a flight with all its known values
    # TODO : ALL save_to_db() methods should be first check that event is not stored before creating it

    # def is_stored(self):
    #     """Look for self in db and return a boolean if flight found or an exception if many flights
    #     have the same or similar fields"""
    #     retrieved_flights = self.retrieve_matching_flights()
    #     if retrieved_flights and len(retrieved_flights) == 1:
    #         retrieved_flight = retrieved_flights[0]
    #         self.astimezone(utc)
    #         if retrieved_flight == self:
    #             self.event_id = retrieved_flight.event_id
    #             return True
    #     elif retrieved_flights:
    #         for retrieved_flight in retrieved_flights:
    #             if retrieved_flight == self:
    #                 self.event_id = retrieved_flight.event_id
    #                 return True
    #         else:
    #             raise Exception("Something is wrong with this flight: {} ".format(self))
    #     return False

    def retrieve_matching_flights(self):
        """Load from Data Base. """
        built_flights = []
        scheduled_begin = self.scheduled_itinerary.begin.replace(tzinfo=None)
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM public.flights '
                           '    WHERE airline_iata_code = %s '
                           '      AND route_id=%s'
                           '      AND scheduled_begin::date=%s;',
                           (self.carrier, self.route.route_id, scheduled_begin.date()))
            flights_data = cursor.fetchall()
            if flights_data:
                built_flights = []
                for flight_data in flights_data:
                    flight_id = flight_data[0]
                    carrier_code = flight_data[1]
                    scheduled_begin = flight_data[3]
                    scheduled_block = flight_data[4]
                    equipment = Equipment(flight_data[5])
                    actual_begin = flight_data[6]
                    actual_block = flight_data[7]
                    scheduled_itinerary = Itinerary.from_timedelta(begin=pytz.utc.localize(scheduled_begin),
                                                                   a_timedelta=scheduled_block)
                    if actual_begin:
                        actual_itinerary = Itinerary.from_timedelta(begin=pytz.utc.localize(actual_begin),
                                                                    a_timedelta=actual_block)
                    else:
                        actual_itinerary = None
                    built_flights.append(Flight(route=self.route, scheduled_itinerary=scheduled_itinerary,
                                                actual_itinerary=actual_itinerary, equipment=equipment,
                                                carrier=carrier_code, event_id=flight_id))
        return built_flights

    def save_to_db(self) -> int:
        # scheduled_begin = self.scheduled_itinerary.begin
        if not self.event_id:
            with CursorFromConnectionPool() as cursor:
                cursor.execute('INSERT INTO public.flights('
                               '            airline_iata_code, route_id, scheduled_begin, '
                               '            scheduled_block, equipment) '
                               'VALUES (%s, %s, %s, %s, %s) '
                               'RETURNING flight_id; ',
                               (self.carrier, self.route.route_id, self.scheduled_itinerary.begin.replace(tzinfo=None),
                                self.duration.as_timedelta(), self.equipment.airplane_code))
                self.event_id = cursor.fetchone()[0]
        return self.event_id

    # def merge_to_db(self) -> int:
    #     # Is this a new route?
    #     if not self.event_id:
    #         stored_flight = self.load_from_db_by_fields(airline_iata_code=self.carrier,
    #                                                     scheduled_begin=self.scheduled_itinerary,
    #                                                     route=self.route)
    #         scheduled_begin = self.scheduled_itinerary._begin.replace(tzinfo=None)
    #         with CursorFromConnectionPool() as cursor:
    #             cursor.execute('INSERT INTO public.flights('
    #                            '            airline_iata_code, route_id, scheduled_begin, '
    #                            '            scheduled_block, equipment)'
    #                            'VALUES (%s, %s, %s, %s, %s) '
    #                            'ON CONFLICT ON CONSTRAINT unique_flight '
    #                            'DO RETURN flight_id;',
    #                            (self.carrier, self.route.route_id, scheduled_begin,
    #                             self.duration.as_timedelta(), self.equipment.airplane_code))
    #             self.event_id = cursor.fetchone()[0]
    #     return self.event_id

    def delete(self):
        """Remove flight from DataBase"""
        with CursorFromConnectionPool() as cursor:
            cursor.execute('DELETE FROM public.flights '
                           '    WHERE flight_id = %s',
                           (self.event_id,))
        # try:
        #     with CursorFromConnectionPool() as cursor:
        #         cursor.execute('DELETE FROM public.flights '
        #                        '    WHERE flight_id = %s',
        #                        (self.event_id,))
        # except psycopg2.IntegrityError:
        #     # TODO : Better build methods directly into the class
        #     print("flight {} ".format(self))
        #     print("Can't be deleted because it belongs to another trip ")
        #     print("Would you rather update it? ")
        #     begin = input("Enter begin time as HHMM :")
        #     duration = input("Enter duration as HHMM :")
        #     self.begin.replace(hour=int(begin[:2]), minute=int(begin[2:]))
        #     self.end = self.begin + Duration.from_string(duration).as_timedelta()
        #     self.update_to_db()

    # def update_to_db(self):
    #     with CursorFromConnectionPool() as cursor:
    #         cursor.execute('UPDATE public.flights '
    #                        'SET airline_iata_code = %s, route_id = %s, scheduled_begin = %s, '
    #                        'scheduled_block = %s, equipment = %s '
    #                        'WHERE flight_id = %s;',
    #                        (self.carrier, self.route.route_id, self.begin,
    #                         self.duration.as_timedelta(), self.equipment.airplane_code, self.event_id))

    #
    #     # This is tricky, because the DH condition is loaded in the duty_days table, not in each flight
    #     # if self.dh != loaded_flight.dh:
    #     #     print(self)
    #     #     answer = input("is flight a DH flight? y/n").upper()
    #     #     if answer[0] == 'Y':
    #     #         self.dh = True
    #     #     else:
    #     #         self.dh = False
    #
    #     if loaded_flight.equipment:
    #         if self.equipment and (self.equipment != loaded_flight.equipment):
    #             print("equipment discrepancy, which one would you like to keep ? ")
    #             print("1. {} ".format(self.equipment))
    #             print("2. {} ".format(loaded_flight.equipment))
    #             option = input()
    #             if option != 1:
    #                 self.equipment = loaded_flight.equipment
    #         else:
    #             self.equipment = loaded_flight.equipment
    #
    @classmethod
    def load_from_db_by_id(cls, flight_id: int):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM public.flights '
                           'INNER JOIN public.routes ON flights.route_id = routes.route_id '
                           'WHERE flights.flight_id=%s', (flight_id,))
            flight_data = cursor.fetchone()
            if flight_data:
                route = Route.load_by_id(route_id=flight_data[2])
                begin = pytz.utc.localize(flight_data[3])
                itinerary = Itinerary.from_timedelta(begin=begin,
                                                     a_timedelta=flight_data[4])
                equipment = Equipment.load_from_db(airplane_code=flight_data[5])
                carrier = flight_data[1]
                return cls(route=route, scheduled_itinerary=itinerary, equipment=equipment,
                           carrier=carrier, event_id=flight_id)

    @classmethod
    def load_from_db_by_fields(cls, airline_iata_code: str, scheduled_begin: datetime, route: Route):
        """Load from Data Base. """
        built_flights = None
        route = Route.load_from_db(name=route.name, origin=route.origin, destination=route.destination)
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM public.flights '
                           '    WHERE airline_iata_code = %s '
                           '      AND route_id=%s'
                           '      AND scheduled_begin::date=%s;',
                           (airline_iata_code, route.route_id, scheduled_begin.date()))
            flights_data = cursor.fetchall()
            if flights_data:
                built_flights = []
                for flight_data in flights_data:
                    flight_id = flight_data[0]
                    carrier_code = flight_data[1]
                    scheduled_begin = flight_data[3]
                    scheduled_block = flight_data[4]
                    equipment = Equipment.load_from_db(airplane_code=flight_data[5])
                    actual_begin = flight_data[6]
                    actual_block = flight_data[7]
                    scheduled_itinerary = Itinerary.from_timedelta(begin=pytz.utc.localize(scheduled_begin),
                                                                   a_timedelta=scheduled_block)
                    if actual_begin:
                        actual_itinerary = Itinerary.from_timedelta(begin=pytz.utc.localize(actual_begin),
                                                                    a_timedelta=actual_block)
                    else:
                        actual_itinerary = None
                    built_flights.append(
                        cls(route=route, scheduled_itinerary=scheduled_itinerary, actual_itinerary=actual_itinerary,
                            equipment=equipment, carrier=carrier_code, event_id=flight_id))
        return built_flights

    @classmethod
    def fetch_all_matching(cls, airline_iata_code: str, scheduled_begin: datetime, route: Route) -> list:
        """Load from Data Base. """
        built_flights = []
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM public.flights '
                           '    WHERE airline_iata_code = %s '
                           '      AND route_id=%s '
                           '      AND scheduled_begin::date=%s; ',
                           (airline_iata_code, route.route_id, scheduled_begin.date()))
            flights_data = cursor.fetchall()
            if flights_data:
                for flight_data in flights_data:
                    flight_id = flight_data[0]
                    carrier_code = flight_data[1]
                    scheduled_begin = flight_data[3]
                    scheduled_block = flight_data[4]
                    equipment = Equipment.load_from_db(flight_data[5])
                    actual_begin = flight_data[6]
                    actual_block = flight_data[7]
                    scheduled_itinerary = Itinerary.from_timedelta(begin=pytz.utc.localize(scheduled_begin),
                                                                   a_timedelta=scheduled_block)
                    if actual_begin:
                        actual_itinerary = Itinerary.from_timedelta(begin=pytz.utc.localize(actual_begin),
                                                                    a_timedelta=actual_block)
                    else:
                        actual_itinerary = None
                    flight = cls(route=route, scheduled_itinerary=scheduled_itinerary,
                                 actual_itinerary=actual_itinerary,
                                 equipment=equipment, carrier=carrier_code,
                                 event_id=flight_id)
                    built_flights.append(flight)

        return built_flights

    def update_to_db(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE public.flights '
                           'SET airline_iata_code = %s, route_id = %s, scheduled_begin = %s, '
                           'scheduled_block = %s, equipment = %s '
                           'WHERE flight_id = %s;',
                           (self.carrier, self.route.route_id, self.begin,
                            self.duration.as_timedelta(), self.equipment.airplane_code, self.event_id))

    def astimezone(self, timezone='local'):
        """Change event's itineraries to given timezone"""
        if timezone != 'local':
            self.scheduled_itinerary.astimezone(begin_timezone=timezone,
                                                end_timezone=timezone)
            if self.actual_itinerary:
                self.actual_itinerary.astimezone(begin_timezone=timezone,
                                                 end_timezone=timezone)
        else:
            self.scheduled_itinerary.astimezone(begin_timezone=self.route.origin.timezone,
                                                end_timezone=self.route.destination.timezone)
            if self.actual_itinerary:
                self.actual_itinerary.astimezone(begin_timezone=self.route.origin.timezone,
                                                 end_timezone=self.route.destination.timezone)

    def __str__(self):
        template = """
        {0.report:%d%b} {0.name:>6s} {0.route.origin} {0.begin:%H%M} {0.route.destination} {0.end:%H%M}\
        {0.duration:2}        {0.equipment}
        """
        return template.format(self)


class DutyDay(object):
    """
    A DutyDay is a collection of Events, it is not a representation of a regular calendar day,
    but rather the collection of Events to be served within a given Duty.
    """

    def __init__(self) -> None:
        self.events = []
        self._credits = {}
        self._report = None

    @property
    def begin(self):
        return self.events[0].begin

    @property
    def end(self):
        return self.events[-1].end

    @property
    def report(self):
        return self._report if self._report else self.events[0].report

    @property
    def release(self):
        return self.events[-1].release

    @property
    def delay(self):
        delay = Duration.from_timedelta(self.begin - self.report) - Duration(60)
        return delay

    @property
    def duration(self):
        """How long is the DutyDay"""
        return Duration.from_timedelta(self.release - self.report)

    @property
    def turns(self):
        return [Duration.from_timedelta(j.begin - i.end) for i, j in zip(self.events[:-1], self.events[1:])]

    @property
    def origin(self):
        return self.events[0].route.origin

    def get_elapsed_dates(self):
        """Returns a list of dates in range [self.report, self.release]"""
        delta = self.release.date() - self.report.date()
        all_dates = [self.report.date() + timedelta(days=i) for i in range(delta.days + 1)]
        return all_dates

    def compute_credits(self, creditator=None):
        """Cares only for block, dh, total and daily"""
        # TODO : Take into consideration whenever there is a change in month
        if creditator:
            creditator.credits_from_duty_day(self)
        else:
            self._credits['block'] = Duration(0)
            self._credits['dh'] = Duration(0)
            for event in self.events:
                event.compute_credits(creditator)
                self._credits['block'] += event._credits['block']
                self._credits['dh'] += event._credits['dh']

            self._credits.update({'daily': self.duration,
                                  'total': self._credits['block'] + self._credits['dh']})
        return [self._credits]

    def append(self, current_duty):
        """Add a duty, one by one  to this DutyDay"""
        self.events.append(current_duty)

    def merge(self, other):
        if self.report <= other.report:
            all_events = self.events + other.events
        else:
            all_events = other.events + self.events
        self.events = []
        for event in all_events:
            self.events.append(event)

    def save_to_db(self, container_trip):
        with CursorFromConnectionPool() as cursor:
            report = self.report.replace(tzinfo=None)
            for flight in self.events:
                if not flight.event_id:
                    # First store flight in DB
                    flight.save_to_db()

                cursor.execute('SELECT duty_day_id FROM public.duty_days '
                               'WHERE flight_id=%s AND trip_id=%s AND trip_date=%s',
                               (flight.event_id, container_trip.number, container_trip.dated))
                flight_to_trip_id = cursor.fetchone()
                if not flight_to_trip_id:
                    cursor.execute('INSERT INTO public.duty_days('
                                   '            flight_id, trip_id, trip_date, '
                                   '            report, dh)'
                                   'VALUES (%s, %s, %s, %s, %s)'
                                   'RETURNING duty_day_id;',
                                   (flight.event_id, container_trip.number, container_trip.dated,
                                    report, flight.dh))
                    flight_to_trip_id = cursor.fetchone()[0]
                report = None
        with CursorFromConnectionPool() as cursor:
            release = self.release.replace(tzinfo=None)
            cursor.execute('UPDATE public.duty_days '
                           'SET rel = %s '
                           'WHERE duty_day_id = %s;',
                           (release, flight_to_trip_id))

    def astimezone(self, timezone='local'):
        """Change event's itineraries to given timezone"""
        for event in self.events:
            event.astimezone(timezone)

    def __str__(self):
        """The string representation of the current DutyDay"""
        rpt = '{:%H%M}'.format(self.report)
        rls = '    '
        body = ''
        if len(self.events) > 1:
            for event, turn in zip(self.events, self.turns):
                # turn = format(turn, '0')
                body = body + event.as_robust_string(rpt, rls, turn)
                rpt = 4 * ''
            rls = '{:%H%M}'.format(self.release)
            body = body + self.events[-1].as_robust_string(rls=rls)
        else:
            rls = '{:%H%M}'.format(self.release)
            body = self.events[-1].as_robust_string(rpt, rls, 4 * '')

        return body


class Trip(object):
    """
    A trip_match is a collection of DutyDays for a specific crew_base
    """

    def __init__(self, number: str, dated: date, crew_position: str, crew_base: Airport) -> object:
        """A trip is identified by a 4 digit number and its report date.
        Trip's report date should be localized in trip's crew_base
        """
        self.number = number
        self.dated = dated
        self.crew_position = crew_position
        self.crew_base = crew_base
        self._credits = {}
        self.duty_days = []

    @classmethod
    def load_by_id(cls, trip_number: str, dated):
        trip = Trip.load_trip_info(trip_number=trip_number, dated=dated)
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT duty_days.flight_id, report, rel, trip_date, dh FROM public.duty_days '
                           'INNER JOIN flights ON duty_days.flight_id = flights.flight_id '
                           'WHERE trip_id = %s AND trip_date = %s '
                           'ORDER BY scheduled_begin ASC;',
                           (int(trip_number), dated))
            trip_data = cursor.fetchall()
            duty_day = None
            if trip_data:
                for row in trip_data:
                    if row[1]:
                        # Beginning of a DutyDay
                        duty_day = DutyDay()
                    flight = Flight.load_from_db_by_id(flight_id=row[0])
                    if not flight:
                        print("Enter flight as DDMMYYYY AC#### ORG HHMM DES HHMM EQU")
                        flight_data = input("v.gr. 23062018 0403 MEX 0700 JFK 1300 7S8")
                        flight = Flight.from_string(flight_data)
                        flight.save_to_db()
                    if row[4]:
                        # dh boolean indicates this flight is a DH flight
                        flight.dh = True
                    duty_day.append(flight)
                    if row[2]:
                        # Ending of a DutyDay
                        trip.append(duty_day)
        return trip

    @classmethod
    def load_trip_info(cls, trip_number: str, dated):
        """
        Used as a simple read from trip information

        """
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * '
                           'FROM trips '
                           'WHERE number = %s AND dated = %s ',
                           (int(trip_number), dated))
            trip_data = cursor.fetchone()
            if trip_data:
                airport = Airport.load_from_db(trip_data[7])
                trip = cls(number=trip_number, dated=trip_data[1], crew_position=trip_data[6], crew_base=airport)
                return trip
            else:
                raise UnstoredTrip(trip_number=trip_number, dated=dated)

    @property
    def report(self):
        return self.duty_days[0].report

    @property
    def release(self):
        return self.duty_days[-1].release

    @property
    def rests(self):
        """Returns a list of all calculated rests between each duty_day"""
        return [Duration.from_timedelta(j.report - i.release) for i, j in zip(self.duty_days[:-1], self.duty_days[1:])]

    @property
    def layovers(self):
        """Returns a list of all layover stations """
        return [duty_day.events[-1].destination for duty_day in self.duty_days]

    @property
    def duration(self):
        "Returns total time away from base or TAFB"
        return Duration.from_timedelta(self.release - self.report)

    def get_elapsed_dates(self):
        """Returns a list of dates in range [self.report, self.release]"""
        delta = self.release.date() - self.report.date()
        all_dates = [self.report.date() + timedelta(days=i) for i in range(delta.days + 1)]
        return all_dates

    def compute_credits(self, creditator=None):

        if creditator:
            return creditator.credits_from_trip(self)
        else:
            self._credits['block'] = Duration(0)
            self._credits['dh'] = Duration(0)
            self._credits['daily'] = Duration(0)
            for duty_day in self.duty_days:
                duty_day.compute_credits(creditator)
                self._credits['block'] += duty_day._credits['block']
                self._credits['dh'] += duty_day._credits['dh']
                self._credits['daily'] += duty_day._credits['daily']
            self._credits.update({'total': self._credits['block'] + self._credits['dh'],
                                  'tafb': self.duration})

    def append(self, duty_day):
        """Simply append a duty_day"""
        self.duty_days.append(duty_day)

    def pop(self, index=-1):
        return self.duty_days.pop(index)

    def __delitem__(self, key):
        del self.duty_days[key]

    def __getitem__(self, key):
        try:
            item = self.duty_days[key]
        except:
            item = None
        return item

    def __setitem__(self, key, value):
        self.duty_days[key] = value

    def get_event_list(self):
        event_list = []
        for duty_day in self.duty_days:
            for event in duty_day.events:
                event_list.append(event)
        return event_list

    def astimezone(self, timezone='local'):
        """Change event's itineraries to given timezone"""
        for duty_day in self.duty_days:
            duty_day.astimezone(timezone)

    def __repr__(self):
        return "{__class__.__name__} {number} dated {dated}".format(__class__=self.__class__, **self.__dict__)

    def __str__(self):
        self.compute_credits()
        header_template = """
        # {0.number}                                                  CHECK IN AT {0.report:%H:%M}
        {0.report:%d%b%Y}
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN        EQ"""

        body_template = """{duty_day}
                     {destination} {rest::}                   {block}BL {dh}CRD {total}TL {daily}DY"""

        footer_template = """

          TOTALS     {total::}TL     {block::}BL     {dh::}CR           {tafb::}TAFB"""

        header = header_template.format(self)
        body = ''

        for duty_day, rest in zip(self.duty_days, self.rests):
            # rest = "{0::}".format(rest)
            body = body + body_template.format(duty_day=duty_day,
                                               destination=duty_day.events[-1].route.destination,
                                               rest=rest,
                                               **duty_day._credits)
        else:
            duty_day = self.duty_days[-1]
            body = body + body_template.format(duty_day=duty_day,
                                               destination='    ',
                                               rest=Duration(0),
                                               **duty_day._credits)

        footer = footer_template.format(**self._credits)
        return header + body + footer

    def save_to_db(self):
        """Save to db should only be concerned with saving a trip regardless of
           its previous status, i.e. if it has been stored before or not

        """
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM public.trips '
                           'WHERE trips.number=%s AND trips.dated=%s', (self.number, self.dated))
            trip_data = cursor.fetchone()

            if not trip_data:
                cursor.execute('INSERT INTO public.trips (number, dated, crew_position, crew_base) '
                               'VALUES (%s, %s, %s, %s);', (self.number, self.dated, self.crew_position,
                                                            self.crew_base.iata_code))
            else:
                raise PreviouslyStoredTrip

        for duty_day in self.duty_days:
            duty_day.save_to_db(self)


class Line(object):
    """ Represents an ordered sequence of events for a given month"""

    def __init__(self, month: str, year: str, crew_member: CrewMember = None) -> None:
        self.duties = []
        self.month = month
        self.year = year
        self.crew_member = crew_member
        self._credits = {}

    def append(self, duty):
        self.duties.append(duty)

    def compute_credits(self, creditator=None):
        self._credits['block'] = Duration(0)
        self._credits['dh'] = Duration(0)
        self._credits['daily'] = Duration(0)
        for duty in self.duties:
            try:
                cr = duty.compute_credits()
                self._credits['block'] += duty._credits['block']
                self._credits['dh'] += duty._credits['dh']
                self._credits['daily'] += duty._credits['daily']
            except AttributeError:
                "Object has no compute_credits() method"
                pass

        if creditator:
            credits_list = creditator.credits_from_line(self)

        return credits_list

    def return_duty(self, dutyId):
        """Return the corresponding duty for the given dutyId"""
        return (duty for duty in self.duties if duty.id == dutyId)

    def __delitem__(self, key):
        del self.duties[key]

    def __getitem__(self, key):
        try:
            item = self.duties[key]
        except:
            item = None
        return item

    def __setitem__(self, key, value):
        self.duties[key] = value

    def __iter__(self):
        return iter(self.duties)

    def astimezone(self, timezone):
        for duty in self.duties:
            if isinstance(duty, Trip):
                duty.astimezone(timezone)

    def return_duty_days(self):
        """Turn all dutydays to a list called dd """
        dd = []
        for element in self.duties:
            if isinstance(element, Trip):
                dd.extend(element.duty_days)
            elif isinstance(element, DutyDay):
                dd.append(element)
        return dd

    def __str__(self):
        return "\n".join(str(d) for d in self.duties)
