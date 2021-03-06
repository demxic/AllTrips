import pytz, sys

from AdminApp.exceptions import UnstoredTrip
from data.database import Database
from models import creditator
from models.scheduleclasses import CrewMember, Airport, Trip, Flight
from models.timeclasses import DateTracker
from models.txtRoster import RosterReader, Liner

summaryFile = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\Resumen de horas\\2019\\201905 - Resumen de horas.txt"
#summaryFile = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\Resumen de horas\\2019\\Rol-2019-05-R.txt"
Database.initialise(database="orgutrip", user="postgres", password="0933", host="localhost")


class Menu:
    """Display a menu and respond to choices when run"""

    def __init__(self):
        self.line = None
        self.choices = {
            "1": self.read_printed_line,
            "2": self.print_line,
            "3": self.credits,
            "4": self.viaticum,
            "5": self.store,
            "6": self.read_flights_summary,
            "7": self.retrieve_duties_from_data_base,
            "8": self.print_components,
            "10": self.quit}

    @staticmethod
    def display_menu():
        print('''
        Orgutrip Menu

        1. Carga tu rol mensual.
        2. Imprime en pantalla tu rol.
        3. Calcula los créditos.
        4. Obtener viáticos.
        5. Almacenar tu rol en la base de datos.
        6. Cargar tu resumen de horas mensuales.
        7. Cargar tiempos por itinerario de la base de datos.
        8. Imprimir cada componente
        10. Quit
        ''')

    def run(self):
        """Display the menu and respond to choices"""
        while True:
            self.display_menu()
            choice = input("¿Qué deseas realizar?: ")
            action = self.choices.get(choice)
            if action:
                action()
            else:
                print("{0} is not a valid choice".format(choice))

    def read_printed_line(self):
        pass

    def print_line(self):
        """Let's print out the roaster"""
        self.line.astimezone(timezone=pytz.timezone('America/Mexico_City'))
        print(self.line)

    def credits(self):
        self.line.astimezone(pytz.timezone('America/Mexico_City'))
        cr = creditator.Creditator('SOB', 'SO01', self.line.month)
        print(creditator.line_credits_header)
        for row in self.line.compute_credits(cr):
            print(row)
        print(self.line._credits['template'].format(**self.line._credits))
        mmmm = cr.month_credits(self.line._credits)
        print("""
                                t_ext_vuelo:    {xblock:2}
                                t_ext_servicio: {xduty:2}
                                t_ext_nocturno: {night:2}
                                maxirre:        {maxirre:2}
                                séptimo día     {day7: >5}
                                prima dominical {sunday: >5}
                                """.format(**mmmm))

    def viaticum(self):
        pass

    def store(self):
        pass

    def read_flights_summary(self):
        """Let's read month's flights summary from a given .txt file"""
        with open(summaryFile, 'r') as fp:
            content = fp.read()
        rr = RosterReader(content)

        # 1. Create Crew Member
        #TODO : No database loading should be done at this stage
        crew_member = CrewMember(**rr.crew_stats)
        crew_member.base = Airport(iata_code=crew_member.base, timezone=pytz.timezone('America/Mexico_City'))
        print("Crew Member :", end=" ")
        print(crew_member)
        print("crew_stats : ", rr.crew_stats)
        print("Carry in within month? ", rr.carry_in)
        print("Roster timeZone ", rr.timeZone)
        print("Roster year and month ", rr.year, rr.month)

        dt = DateTracker(rr.year, rr.month, rr.carry_in)
        print("\ndatetracker for ", dt)

        print("\nCreating a Liner")
        liner = Liner(date_tracker=dt, roster_days=rr.roster_days, crew_member=crew_member,
                      line_type='actual_itinerary')
        liner.build_line()
        self.line = liner.line
        self.line.crew_member = crew_member

    def retrieve_duties_from_data_base(self):
        for duty in self.line.duties:
            if isinstance(duty, Trip):
                #TODO : Aquí me quedé. Ahora resulta que los números de trip pueden cambiar
                try:
                    stored_trip = Trip.load_by_id(trip_number=duty.number, dated=duty.dated)
                except UnstoredTrip:
                    # TODO : This is all messy, try using analogous code from the AdminApp
                    for flight in duty.get_event_list():
                        loaded_flight = Flight.load_from_db_by_fields(
                            airline_iata_code=flight.carrier,
                            scheduled_begin=flight.actual_itinerary.begin,
                            route=flight.route)[0]
                        flight.scheduled_itinerary = loaded_flight.scheduled_itinerary
                        flight.equipment = loaded_flight.equipment
                        flight.event_id = loaded_flight.event_id
                    duty.astimezone(timezone=pytz.timezone('America/Mexico_City'))
                    print(duty)
                    duty.astimezone(timezone=pytz.utc)
                else:
                    for flight, loaded_flight in zip(duty.get_event_list(), stored_trip.get_event_list()):
                        flight.scheduled_itinerary = loaded_flight.scheduled_itinerary
                        flight.equipment = loaded_flight.equipment
                        flight.event_id = loaded_flight.event_id

    def print_components(self):
        pass

    def quit(self):
        answer = input("¿Deseas guardar los cambios? S/N").upper()
        if answer[0] == 'S':
            self.line.crew_member.update_to_db()


        print("adiós")
        sys.exit(0)


if __name__ == '__main__':
    Menu().run()