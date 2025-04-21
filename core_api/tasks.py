from celery import shared_task
from django.db import connection
from core_api.queries.notification_option import ApiSpecialSqlNotificationOption
from datetime import datetime
import pytz

@shared_task
def send_print_tasked():
    cursor = connection.cursor()
    pst_timezone = pytz.timezone('US/Pacific')
    now = datetime.now().astimezone(pst_timezone)
    formatted_time = now.strftime("%A %I %p")

    listNotificationOption = ApiSpecialSqlNotificationOption.get_notification_option_sql_ct_id(cursor)
    
    for notificationOptions in listNotificationOption:
        for notificationOptionTime in notificationOptions[1]:

            rangeOfTime = ApiSpecialSqlNotificationOption.get_range(notificationOptions[2])
            TimeOfSent = ApiSpecialSqlNotificationOption.format_time_string(notificationOptionTime)
            booking_info = ApiSpecialSqlNotificationOption.get_public_id(cursor, notificationOptions[0], rangeOfTime)
            send_email_function = ApiSpecialSqlNotificationOption.send_email(booking_info)

            #Saved = f"ID: {notificationOptions[0]} TIME: {TimeOfSent} NOW: {formatted_time} RANGE {notificationOptions[2]} RANGETIME: {rangeOfTime} PUBLIC IDS: {booking_info}"
            Saved = send_email_function
            print(Saved)