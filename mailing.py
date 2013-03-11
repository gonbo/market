#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
from flask_mail import Message
from flask import url_for, current_app

def send_awaiting_confirm_mail(user):
    """
    Send the awaiting for confirmation mail to the user.
    """
    subject = "We're waiting for your confirmation!"
    mail_to_be_send = Message(subject=subject, recipients=[user['email']])
    active_code = uuid.uuid4();
    confirmation_url = url_for('account.activate_user', uid=user['id'],
            _external=True, code=active_code)
    mail_to_be_send.body = "Dear %s, click the following url to confirm: %s" % \
            (user['email'], confirmation_url)
    current_app.redis.hset("account:%s" % user['id'], 'active_code', active_code)
    current_app.mail.send(mail_to_be_send)


def send_subscription_confirm_mail(user):
    subject = "Welcome!!"
    mail_to_be_send = Message(subject=subject, recipients=[user['email']])
    mail_to_be_send.body = "Congratulaition!"
    current_app.mail.send(mail_to_be_send)


def send_reset_password_mail(email):
    """
    Send a reset mail to user, allow the user to reset password.
    """
    subject = "Reset Password"
    mail_to_be_send = Message(subject=subject, recipients=[email])
    reset_code = uuid.uuid4()
    reset_url = url_for('account.reset_password', _external=True, code=reset_code)
    mail_to_be_send.body = "Dear %s, click the following url to reset your password:%s" % \
            (email, reset_url)
    current_app.redis.set('reset:%s:email' % reset_code, email)
    current_app.mail.send(mail_to_be_send)
