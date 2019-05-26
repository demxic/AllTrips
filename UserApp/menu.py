
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
        pass

    def credits(self):
        pass

    def viaticum(self):
        pass

    def store(self):
        pass

    def read_flights_summary(self):
        pass

    def retrieve_duties_from_data_base(self):
        pass


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