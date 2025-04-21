from datetime import datetime, timedelta
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.conf import settings

class ApiSpecialSqlNotificationOption:

    @staticmethod
    def get_notification_option_sql_ct_id(cursor):
        query = """--sql
            SELECT
                company_id, report_frequency, report_range
            FROM "core_backend_notificationoption" _notificationoption
        """

        cursor.execute(query)
        result = cursor.fetchall()
        if result is not None:
            return result
        
        return None

    @staticmethod
    def get_public_id(cursor, company_id, range_of_time):
        query = """SELECT 
                    _booking.public_id, _contact.email, _contact_r.email
                FROM core_backend_booking _booking 
                    INNER JOIN core_backend_booking_companies _booking_companies 
                        ON _booking_companies.booking_id = _booking.id 
                    INNER JOIN core_backend_event _event
                        ON _event.booking_id = _booking.id
                    LEFT JOIN core_backend_company_contacts _company_contacts
                        ON _company_contacts.company_id = _booking_companies.company_id
                    LEFT JOIN core_backend_contact _contact
                        ON _contact.id = _company_contacts.contact_id
                    LEFT JOIN core_backend_requester _requester
                        ON _requester.id = _event.requester_id
                    LEFT JOIN core_backend_user _user
                        ON _user.id = _requester.user_id
                    LEFT JOIN core_backend_user_contacts _user_contacts
                        ON _user_contacts.user_id = _user.id
                    LEFT JOIN core_backend_contact _contact_r
                        ON _contact_r.id = _user_contacts.contact_id
                WHERE _booking_companies.company_id = %s;
            """ % (company_id)#, range_of_time)

        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) > 0:
            return result
        
        return None

    @staticmethod
    def format_time_string(time_string):
        parts = time_string.split()
        day = parts[0]
        time_part = parts[1]
        am_pm = parts[2]

        hour_part = time_part.split(':')[0] if ':' in time_part else time_part
        #minute_part = time_part.split(':')[1] if ':' in time_part else '00'

        formatted_hour = f"{int(hour_part):02}"
        #formatted_minute = f"{int(minute_part):02}"

        return f"{day} {formatted_hour} {am_pm.upper()}"

    @staticmethod
    def get_range(rangeOfTime):
        numberRange = 0
        if numberRange == "Fourteen days": 
            numberRange = 14
        elif numberRange == "Seven days": 
            numberRange = 7
        elif numberRange == "Three days": 
            numberRange = 3
        elif numberRange == "One days": 
            numberRange = 1
        elif numberRange == "Today": 
            numberRange == 1
            

        # Define the current date (e.g., "today")
        today = datetime.now().strftime('%Y-%m-%d')  # Replace with today's date dynamically using datetime.now()

        # Calculate the range for "Fourteen days"
        start_date = datetime.strptime(today, '%Y-%m-%d')
        end_date = start_date + timedelta(days=numberRange)
        date_range = ""

        # Format the dates
        if numberRange != 0:
            date_range = f"AND start_at BETWEEN '{start_date.strftime('%Y-%m-%d')} 00:00:00-04' AND '{end_date.strftime('%Y-%m-%d')} 24:00:00-04'"

        return date_range

    def send_email(booking_info):
        info = ""
        email = ""
        if booking_info is not None:
            email = booking_info[0][1]
            for book_info in booking_info:
                info = f"{info}\n{book_info[0]}\n"

        subject = "Bookings Info"
        message = "HELLO"#info
        from_email = settings.EMAIL_HOST_USER
        recipient = ['gabrielchacon200269@gmail.com']#[email]
        if message != '' and recipient != ['']:
            try:
                msg = EmailMultiAlternatives(subject, message, from_email, to=recipient)
                msg.attach_alternative(message, "text/html")
                msg.send()
                print("sended",recipient,message,from_email,subject)
            except:
                return settings.EMAIL_HOST_USER
            return 1
        else:
            # In reality we'd use a form class
            # to get proper validation errors.
            return 0
