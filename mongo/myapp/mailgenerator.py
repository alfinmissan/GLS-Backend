from django.core.mail import EmailMessage, get_connection
from django.template.loader import get_template
from django.conf import settings
from rest_framework.response import Response
from django.template import Context
from django.core.mail import send_mail

def email(msg,subject,recipient):
    subject = subject
    message = get_template("gridemailtemplate.html").render({"data":msg})
    email_from = settings.SERVER_EMAIL
    recipient_list = recipient
    # send_mail(subject, message, email_from, recipient_list)
    mail = EmailMessage(
        subject=subject,
        body=message,
        from_email=email_from,
        to=recipient,
    )
    mail.content_subtype = "html"
    return mail.send()
    return Response(data=message)

def user_registered_mail(msg,subject,recipient):
    subject = subject
    message = get_template("user_registration_confirmation.html").render({"data":msg})
    email_from = settings.SERVER_EMAIL
    recipient_list = recipient
    # send_mail(subject, message, email_from, recipient_list)
    mail = EmailMessage(
        subject=subject,
        body=message,
        from_email=email_from,
        to=recipient_list,
    )
    mail.content_subtype = "html"
    return mail.send()
    return Response(data=message)


