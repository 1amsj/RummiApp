from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    help = 'Show event data'

    def handle(self, *args, **options):
        url = 'http://127.0.0.1:8000/api/v1/events/interpretation/?_include_booking=true'
        token = input("Ingrese el token Bearer: ")
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            event_data = response.json()

            # Mostrar los datos del evento
            for event in event_data:
                print(f"ID: {event['id']}")
                print(f"Descriptión: {event['description']}")
                print(f"Start_at: {event['start_at']}")
                print(f"End_at: {event['end_at']}")
                print("")

        else:
            print(f"Error to extract data of fields. Status Code: {response.status_code}")


# Llama al comando desde la línea de comandos
# python manage.py show_event_data