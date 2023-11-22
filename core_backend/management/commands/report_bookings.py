from django.core.management.base import BaseCommand
import requests
from datetime import datetime
import csv

class Command(BaseCommand):
    help = 'Show event data'

    def handle(self, *args, **options):
        url = 'https://core-communications-rcore-be-prod.us-east-1.elasticbeanstalk.com/api/v1/events/interpretation/?_include_booking=true'
        url_languages = 'https://core-communications-rcore-be-prod.us-east-1.elasticbeanstalk.com/api/v1/languages'
        url_company = 'https://core-communications-rcore-be-prod.us-east-1.elasticbeanstalk.com/api/v1/companies'
        token = input("Enter the token Bearer: ")
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers)

        response_languages = requests.get(url_languages, headers=headers)
        response_company = requests.get(url_company, headers=headers)
        
        if response_languages.status_code == 200:
            language_data = response_languages.json()
            language_mapping = {language['alpha3']: language['name'] for language in language_data}
        else:
            print(f"Error to extract language data. Status Code: {response_languages.status_code}")
            return
        
        if response_company.status_code == 200:
            company_data = response_company.json()
            company_mapping = {company['id']: company['name'] for company in company_data}
        else:
            print(f"Error to extract language data. Status Code: {response_company.status_code}")
            return

        if response.status_code == 200:
            event_data = response.json()

            with open('job_report.csv', 'w', newline='') as csvfile:
                fieldnames = ['ID', 'Clinic', 'Language', 'Operator', 'Type of Appointment', 'Authorized',
                              'Authorized By', 'DOS', 'Scheduled Time', 'Interpreter Start Time',
                              'Interpreter Arrive Time', 'Interpreter End Time', 'Patient First Name',
                              'Patient Last Name', 'DOB', 'DOI', 'Claim Number', 'Clinic Addres', 
                              'Clinic City', 'Clinic State', 'Clinic Zip', 
                              'Interpreter First Name', 'Interpreter Last Name',
                              'Certificate', 'Doctor First Name', 'Doctor Last Name', 'Public_id']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for event in event_data:
                    start_at = event['start_at']
                    arrive_at = event['arrive_at']
                    end_at = event['end_at']
                    if "." in start_at or "." in end_at or "." in arrive_at:
                        datetime_obj_start = datetime.strptime(start_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                        datetime_obj_arrive = datetime.strptime(arrive_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                        datetime_obj_end = datetime.strptime(end_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                    else:
                        datetime_obj_start = datetime.strptime(start_at, "%Y-%m-%dT%H:%M:%SZ")
                        datetime_obj_arrive = datetime.strptime(arrive_at, "%Y-%m-%dT%H:%M:%SZ")
                        datetime_obj_end = datetime.strptime(end_at, "%Y-%m-%dT%H:%M:%SZ")
                    date_only_start = datetime_obj_start.date()
                    time_only_start = datetime_obj_start.time()
                    time_only_arrive = datetime_obj_arrive.time()
                    time_only_end = datetime_obj_end.time()

                    date_of_injury = event.get('date_of_injury')
                    claim_number = event.get('claim_number')

                    language_alpha3 = event['booking']['target_language_alpha3']
                    language_name = language_mapping.get(language_alpha3, '')
                    
                    companay_id = event['authorizations'][0]['company'] if event['authorizations'] != [] else ''
                    company_name = company_mapping.get(companay_id, '')

                    writer.writerow({
                        'ID': event['id'],
                        'Clinic': event['booking']['companies'][0]['name'],
                        'Language': language_name,
                        'Operator': f"{event['booking']['operators'][0]['first_name']} {event['booking']['operators'][0]['last_name']}"
                                    if event['booking']['operators'] != [] else '',
                        'Type of Appointment': event['description'],
                        'Authorized': 'Yes' if event['authorizations'] != [] else 'No',
                        'Authorized By': company_name ,
                        'DOS': date_only_start,
                        'Scheduled Time': time_only_start,
                        'Interpreter Start Time': time_only_start,
                        'Interpreter Arrive Time': time_only_arrive,
                        'Interpreter End Time': time_only_end,
                        'Patient First Name': event['affiliates'][0]['recipient']['first_name'],
                        'Patient Last Name': event['affiliates'][0]['recipient']['last_name'],
                        'DOB': event['affiliates'][0]['recipient']['date_of_birth'],
                        'DOI': date_of_injury if date_of_injury is not None else '',
                        'Claim Number': claim_number if claim_number is not None else '',
                        'Clinic Addres': event['booking']['companies'][0]['locations'][0]['address']
                                        if event['booking']['companies'][0]['locations'] != [] else '',
                        'Clinic City': event['booking']['companies'][0]['locations'][0]['city']
                                        if event['booking']['companies'][0]['locations'] != [] else '',
                        'Clinic State': event['booking']['companies'][0]['locations'][0]['state']
                                        if event['booking']['companies'][0]['locations'] != [] else '',
                        'Clinic Zip': event['booking']['companies'][0]['locations'][0]['zip']
                                        if event['booking']['companies'][0]['locations'] != [] else '',
                        'Interpreter First Name': event['booking']['services'][0]['provider']['first_name'] 
                                                if event['booking']['services'] != [] else '',
                        'Interpreter Last Name': event['booking']['services'][0]['provider']['last_name'] 
                                                if event['booking']['services'] != [] else '',
                        'Certificate': event['booking']['service_root']['name'],
                        'Doctor First Name': event['requester']['first_name'],
                        'Doctor Last Name': event['requester']['last_name'],
                        'Public_id': event['booking']['public_id']
                    })

            print("Data saved to event_data.csv successfully.")

        else:
            print(f"Error to extract data of fields. Status Code: {response.status_code}")