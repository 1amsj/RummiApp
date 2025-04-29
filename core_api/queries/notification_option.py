from datetime import datetime, timedelta
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from core_backend import settings

class ApiSpecialSqlNotificationOption:

    @staticmethod
    def get_notification_option_sql(cursor):
        query = """--sql
            SELECT
                company_id, report_frequency, report_range, report_receiver
            FROM "core_backend_notificationoption" _notificationoption
        """

        cursor.execute(query)
        result = cursor.fetchall()
        if result is not None:
            return result
        
        return None

    @staticmethod
    def get_booking_info(cursor, company_id, range_of_time):
        query = """SELECT 
                    _booking.public_id, _contact_c.email, _contact_r.email
                FROM core_backend_booking _booking 
                    INNER JOIN core_backend_booking_companies _booking_companies 
                        ON _booking_companies.booking_id = _booking.id 
                    INNER JOIN core_backend_event _event
                        ON _event.booking_id = _booking.id
                    LEFT JOIN core_backend_company_contacts _company_contacts
                        ON _company_contacts.company_id = _booking_companies.company_id
                    LEFT JOIN core_backend_contact _contact_c
                        ON _contact_c.id = _company_contacts.contact_id
                    LEFT JOIN core_backend_requester _requester
                        ON _requester.id = _event.requester_id
                    LEFT JOIN core_backend_user _user
                        ON _user.id = _requester.user_id
                    LEFT JOIN core_backend_user_contacts _user_contacts
                        ON _user_contacts.user_id = _user.id
                    LEFT JOIN core_backend_contact _contact_r
                        ON _contact_r.id = _user_contacts.contact_id
                WHERE _booking_companies.company_id = %s %s;
            """ % (company_id, range_of_time)

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

        formatted_hour = f"{int(hour_part):02}"

        return f"{day} {formatted_hour} {am_pm.upper()}"

    @staticmethod
    def get_range(rangeOfTime):
        numberRange = -1
        if rangeOfTime == "Fourteen days": numberRange = 14
        elif rangeOfTime == "Seven days": numberRange = 7
        elif rangeOfTime == "Three days": numberRange = 3
        elif rangeOfTime == "One day": numberRange = 1
        elif rangeOfTime == "Today": numberRange = 0
            
        today = datetime.now().strftime('%Y-%m-%d')
        
        start_date = datetime.strptime(today, '%Y-%m-%d')
        end_date = start_date + timedelta(days=numberRange)
        date_range = ""

        # Format the dates
        if numberRange >= 0:
            date_range = f"AND start_at BETWEEN '{start_date.strftime('%Y-%m-%d')} 00:00:00-04' AND '{end_date.strftime('%Y-%m-%d')} 24:00:00-04'"

        return date_range

    def get_info_for_email(booking_info, email_info):
        info = ""
        email = []
        if booking_info is not None:
            
            if email_info == "Clinic":
                email.append(booking_info[0][1])
            elif email_info == "Requester":
                for info_email in booking_info:
                    email.append(info_email[1])
            else:
                email.append(email_info)

            for book_info in booking_info:
                info += f"{book_info[0]}\n"
                
        if info != '' and len(email) > 0:
            return [info, email]
        else:
            return ''

    def send_email_book_info(send_email_info):
        if send_email_info != '':
            subject = "Bookings Info"
            message = send_email_info[0]
            from_email = settings.EMAIL_HOST_USER
            recipient = send_email_info[1]
            try:
                msg = EmailMultiAlternatives(subject, message, from_email, to=recipient)
                msg.attach_alternative(message, "text/html")
                msg.send()
            except BadHeaderError:
                return BadHeaderError
            return 1
        else:
            return 0
