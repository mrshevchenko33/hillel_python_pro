import os
from celery import Celery
import smtplib, ssl
from dotenv import load_dotenv

load_dotenv()
app = Celery('tasks', broker='pyamqp://guest@localhost//')

@app.task
def send_mail(recipient, subject, text):
    sender_email = 'mrshevchenko33@gmail.com'
    receiver_email = recipient
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465
    username = 'mrshevchenko33@gmail.com'
    password = os.getenv('EMAIL_PASSWORD')

    message = f"From: {sender_email}\nTo: {receiver_email}\nSubject: {subject}\n\n{text}.".encode('utf-8')

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as smtp:
            smtp.login(username, password)
            smtp.sendmail(sender_email, receiver_email, message)
            print('Email sent successfully.')
    except Exception as e:
        print(f'Error: {e}')


