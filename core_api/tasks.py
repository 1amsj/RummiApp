from celery import shared_task
from django.db import connection
from core_api.queries.notification_option import ApiSpecialSqlNotificationOption
from datetime import datetime
import pytz

@shared_task
def send_clinic_email():
    cursor = connection.cursor()
    pst_timezone = pytz.timezone('US/Pacific')
    now = datetime.now().astimezone(pst_timezone)
    formatted_time = now.strftime("%A %I %p")

    listNotificationOption = ApiSpecialSqlNotificationOption.get_notification_option_sql(cursor)
    send_email_info = ''
    
    for notificationOptions in listNotificationOption:
        try:
            for notificationOptionTime in notificationOptions[1]:

                rangeOfTime = ApiSpecialSqlNotificationOption.get_range(notificationOptions[2])
                TimeOfSent = ApiSpecialSqlNotificationOption.format_time_string(notificationOptionTime)
                booking_info = ApiSpecialSqlNotificationOption.get_booking_info(cursor, notificationOptions[0], rangeOfTime)
                send_email_info = ApiSpecialSqlNotificationOption.get_info_for_email(booking_info, notificationOptions[3])
                
                if(TimeOfSent == formatted_time):
                    send_email_info = ApiSpecialSqlNotificationOption.get_info_for_email(booking_info, notificationOptions[3])
                    send_email_function = ApiSpecialSqlNotificationOption.send_email_book_info(send_email_info)
                    print(send_email_function)
        except:
            print("Err Or Not Have Report")