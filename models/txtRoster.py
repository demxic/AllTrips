"""
Created on 29/12/2015

@author: Xico

A bidline reader should return a bidline

"""
from UserApp.userappregex import roster_data_RE, crewstats_no_type, carryInRE, non_trip_RE, roster_trip_RE, \
    airItineraryRE


class RosterReader(object):
    def __init__(self, content: str = None):
        """
        Receives an fp iterable and reads out all roster information
        """
        self.content = content
        self.crew_stats = None
        self.carry_in = None
        self.roster_days = []
        self.timeZone = None
        self.month = None
        self.year = None
        self.read_data()

    def read_data(self):
        """
        Search for all needed information
        Data may be of three types
        - roster_day
        - heather of a roster file
        - crew_stats or information of the crew member
        """

        roster_data = roster_data_RE.search(self.content).groupdict()
        self.month = roster_data['month']
        self.year = int(roster_data['year'])
        # Found all crewMember stats. Of particular importance are the
        # timeZone of the given bidLine.
        # TODO : There should be only one type of crewstats
        crew_stats = crewstats_no_type.search(roster_data['header']).groupdict()
        # if not crew_stats:
        #     crew_stats = crewstats_with_type.search(roster_data['header']).groupdict()
        self.timeZone = crew_stats.pop('timeZone')
        self.crew_stats = crew_stats

        # Month should start in number 1 or else there is a carry in
        cin = carryInRE.search(roster_data['body'])
        first_day_in_roster = cin.groupdict()['day']
        self.carry_in = int(first_day_in_roster) > 1

        # What is the line's first duty?
        # first_duty = first_duty_RE.search(roster_data['body']).group()

        # Search and store all Ground Duties and Markers
        ground_duty_rows = list()
        for roster_day in non_trip_RE.finditer(roster_data['body']):
            ground_duty_rows.append(roster_day.groupdict())

        # Search and store all Trips
        for trip_row_match in roster_trip_RE.finditer(roster_data['body']):
            roster_day = trip_row_match.groupdict()
            flights = []
            for flight in airItineraryRE.finditer(roster_day['flights']):
                flights.append(flight.groupdict())
            roster_day['flights'] = flights
            self.roster_days.append(roster_day)

        for row in ground_duty_rows:
            index = self.index_where_to_insert(row)
            self.roster_days.insert(index, row)

    def index_where_to_insert(self, reserve):
        index = 0
        for list_index, trip_row in enumerate(self.roster_days):
            if reserve['day'] >= trip_row['day']:
                index = list_index + 1
        return index

