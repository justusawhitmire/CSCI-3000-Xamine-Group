from background_task import background
from django.contrib.auth.models import Group
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils.html import strip_tags

from xamine.models import Order, AppSetting



def send_email(to_email, from_email, subject, html_content):
    """ Defines how to send generic email"""

    if AppSetting.get_setting("EMAIL_TOGGLE") != 'True':
        return

    if isinstance(to_email, str):
        to_email = [to_email]

    # Create non-HTML version of message
    text_content = strip_tags(html_content)

    # create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")

    # Send the email
    msg.send()
    return

"""@background(schedule= remnd == now)
def send_reminder(Order):
    import smtplib
    from email.mime.text import MIMEText
    from socket import gaierror
    ord = Order.objects.get(pk=order_id)

    # now you can play with your code. Let’s define the SMTP server separately here:
    port = 587 
    smtp_server = "smtp.gmail.com"
    login = "xamineinc@gmail.com" 
    password = os.environ.get('EMAIL_PASS')

    # specify the sender’s and receiver’s email addresses
    sender = "xamineinc@gmail.com"
    receiver = ord.patient.email_info

    # type your message: use two newlines (\n) to separate the subject from the message body, and use 'f' to  automatically insert variables in the text
    message = f"""\
    """Subject: Hello Xamine Patient
    To: {receiver}
    From: {sender}

    You are scheduled for an appointment on {appt}

    See you then!

    Xamine Group"""""""

    try:
        #send your message with credentials specified above
        with smtplib.SMTP(smtp_server, port) as server:
            server.login(login, password)
            server.sendmail(sender, receiver, message)

        # tell the script to report if your message was sent or which errors need to be fixed 
        print('Sent')
    except (gaierror, ConnectionRefusedError):
        print('Failed to connect to the server. Bad connection settings?')
    except smtplib.SMTPServerDisconnected:
        print('Failed to connect to the server. Wrong user/password?')
    except smtplib.SMTPException as e:
        print('SMTP error occurred: ' + str(e))"""


@background(schedule=5)
def send_notification(order_id):
    """ Send notification to correct group of users """

    # Grab correct order via order_id and set our from address
    ord = Order.objects.get(pk=order_id)
    sender = 'xamineinc@gmail.com'

    # If level is 1, send to the receptionists
    if ord.level_id == 1:
        subject = f"New Patient Referral: {ord.patient.full_name}"
        body = f"The office of {ord.patient.doctor.get_full_name()} has referred {ord.patient.full_name}."

        recipients = Group.objects.get(name="Receptionists").user_set.values_list('email', flat=True)

    # If level is 2, send to the technicians from the order's assigned team
    elif ord.level_id == 2:
        subject = f"Patient Checked In: {ord.patient.full_name}"
        body = f"Patient checked in for their appointment."

        recipients = ord.team.technicians.values_list('email', flat=True)

    # If level is 2, send to the radiologists from the order's assigned team
    elif ord.level_id == 3:
        subject = f"Imaging Complete: {ord.patient.full_name}"
        body = f"Patient imaging has been completed and is ready for analysis."

        recipients = ord.team.technicians.values_list('email', flat=True)

    # if level is 4, send to the patient's doctor
    elif ord.level_id == 4:
        subject = f"Order Complete: {ord.patient.full_name}"
        body = f"Patient imaging and analysis has been completed and is ready for review."

        recipients = [ord.patient.doctor.email]
    else:
        return

    # Grab order URL, set up body of message, and send email
    url = reverse('order', kwargs={'order_id': ord.id})
    body += f"<br><br><a href='{url}' target='_blank'>Click Here to View</a>"

    send_email(list(recipients), sender, subject, body)
