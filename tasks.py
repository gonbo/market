import uuid
from celery import Celery
from fmail import Message
from utils import signer, mail, redis_db, DEFAULT_MAIL_SENDER

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def bid():
    pass

@celery.task
def sell():
    pass

@celery.task
def send_register_confirm_mail(user, confirm_url):
    """
    Send the awaiting for confirmation mail to the user.
    """
    subject = "We're waiting for your confirmation!"
    mail_to_be_send = Message(subject=subject, sender=DEFAULT_MAIL_SENDER, recipients=[user['email']])
    signature = signer.sign(str(user['id']))
    confirmation_url = confirm_url + "?sign=" + signature
    mail_to_be_send.body = "Dear %s, click the following url to confirm: %s" % \
            (user['email'], confirmation_url)
    mail.send(mail_to_be_send)


@celery.task
def send_subscription_confirm_mail(user):
    subject = "Welcome!!"
    mail_to_be_send = Message(subject=subject, sender=DEFAULT_MAIL_SENDER, recipients=[user['email']])
    mail_to_be_send.body = "Congratulaition!"
    mail.send(mail_to_be_send)


@celery.task
def send_reset_password_mail(email, reset_url):
    """
    Send a reset mail to user, allow the user to reset password.
    """
    subject = "Reset Password"
    mail_to_be_send = Message(subject=subject, recipients=[email])
    reset_code = uuid.uuid4()
    reset_url =  reset_url + "?code=" + reset_code
    mail_to_be_send.body = "Dear %s, click the following url to reset your password:%s" % \
            (email, reset_url)
    redis_db.set('reset:%s:email' % reset_code, email)
    mail.send(mail_to_be_send)
