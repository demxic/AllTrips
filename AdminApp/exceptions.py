"""Module to catch and handle expected exceptions"""


class TripBlockError(Exception):

    def __init__(self, expected_block_time, trip):
        super().__init__("Trip's expected block time {} is different from actual {}"
                         "".format(expected_block_time, trip.duration))
        self.expected_block_time = expected_block_time
        self.trip = trip

    def delete_invalid_duty_days(self):
        pass


class UnbuiltTripError(Exception):
    pass


class PreviouslyStoredTrip(Exception):
    pass


class DutyDayBlockError(Exception):

    def __init__(self, duty_day_dict: dict, duty_day) -> None:
        super().__init__("DutyDay's expected daily time {} is different from actual {}".format(duty_day_dict['dy'],
                                                                                               duty_day.duration))
        self.duty_day_dict = duty_day_dict
        self.duty_day = duty_day

    def delete_invalid_flights(self):
        found_one_after_dh = False
        for flight in self.duty_day.events:
            if not flight.name.isnumeric() or found_one_after_dh:
                # TODO : Instead of deleting flight, try erasing only the inconsistent data
                print("Dropping from DataBase flight: {} ".format(flight))
                flight.delete()
                found_one_after_dh = True


class UndefinedBlockTime(Exception):
    def __init__(self, flight_dict, flight):
        super().__init__("No se ha podido deteriminar el blk time del vuelo {}/{}".format(
                flight.name, flight.begin))
        self.flight_dict = flight_dict
        self.flight = flight


class UnsavedRoute(Exception):
    def __init__(self, route):
        super().__init__("route: {} is not stored in the data base".format(route))
        self.route = route


class UnsavedAirport(Exception):
    def __init__(self, airport_iata_code):
        super().__init__("airport: {} is not stored in the data base".format(airport_iata_code))
        self.airport_iata_code = airport_iata_code


class UnstoredTrip(Exception):
    def __init__(self, trip_number, dated):
        super().__init__("Trip {} dated  {} not found in the Data Base"
                         "".format(trip_number, dated))
        self.trip_number = trip_number
        self.dated = dated


