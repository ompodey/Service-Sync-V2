from tools.workers import celery
from models import *
from datetime import datetime, timedelta
from tools.mailer import send_email
from collections import defaultdict
from flask import render_template
from celery.schedules import crontab


@celery.on_after_finalize.connect #lifecycle hook.
def setup_periodic_tasks(sender, **kwargs):

    # sender.add_periodic_task(10.0, send_daily_reminder.s(), name='sends every 10 seconds')

    sender.add_periodic_task(crontab(hour=5, minute=30),  # 5:30 AM UTC corresponds to 11:00 AM IST
        send_daily_reminder.s(),name='Send daily reminders at 11:00 AM IST')
    
    # sender.add_periodic_task(15.0, send_pending_service_reminder.s(), name='sends every 15 seconds')

    sender.add_periodic_task(crontab(hour=13, minute=30),  # 1:30 PM UTC corresponds to 7:00 PM IST
        send_pending_service_reminder.s(),name='Send pending service reminders at 7:00 PM IST')
    
    sender.add_periodic_task(crontab(hour=4, minute=30, day_of_month=1),  # 10:00 AM IST on the 1st day of every month
                        send_monthly_report.s(),name='Send monthly reminders at 10:00 AM IST')


    sender.add_periodic_task(20.0, send_monthly_report.s(), name='sends every 20 seconds'),  







@celery.task
def send_daily_reminder():
    pasttime = datetime.now() - timedelta(hours=24)
    inactivecustomers = Members.query.filter(Members.last_logged_in < pasttime).filter_by(role='customer').all()
    mems = inactivecustomers
    for mem in inactivecustomers:
    
        html=render_template('daily_reminder.html',user_name=mem.name)
        send_email(mem.email, "Daily Reminder", body=html)
        print('Email sent to : ', mem.name)
    return ('Email sent to : ', len(inactivecustomers), 'customers')




@celery.task
def send_pending_service_reminder():
    # Fetch all pending requests
    pendingreq = Booking.query.filter_by(status='pending').all()
    profreq = {}


    for booking in pendingreq:
        professional = Profressinal.query.filter_by(id=booking.professional_id).first()
        customer_name = Members.query.filter_by(id=booking.user_id).first().name

        if professional.name not in profreq:
            profreq[professional.name] = set() 

        profreq[professional.name].add(customer_name)

   
    for professional_name, customer_set in profreq.items():
        professional = Profressinal.query.filter_by(name=professional_name).first()
        professional_email = professional.email
        customer_list_html = ''.join(f"{customer}, " for customer in customer_set)  # Create an HTML list

  
        email_body = render_template(
            "pending_request_reminder.html",
            professional_name=professional_name,
            customer_list=customer_list_html
        )
        send_email(professional_email,"Pending Service Reminder",body=email_body)

    return f"Emails sent to {len(profreq)} pending requests."


@celery.task
def send_monthly_report():
    one_month_date = datetime.now() - timedelta(days=30)
    cutomers = Members.query.filter_by(role='customer')
    for customer in cutomers:
        customer_bookings = Booking.query.filter_by(user_id=customer.id).filter(Booking.service_date >= one_month_date).all()
        total_amount = 0
        booking_details = []
        for booking in customer_bookings:
            total_amount += booking.booking_charge
            booking_details.append({
                'professional_name': booking.professional.name,
                'service_name': booking.professional.servicename,
                'service_date': booking.service_date,
                'service_time': booking.service_time,
                'status': booking.status,
                'booking_charge': booking.booking_charge
            })
        html = render_template('monthly_report.html', customer_name=customer.name, total_amount=total_amount, booking_details=booking_details)
        send_email(customer.email, "Monthly Report", html )
    return ('Monthly report Sent.')