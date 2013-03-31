#!/usr/bin/env python
# -*- coding: utf-8 -*-
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, g
from flask.ext.wtf import TextField, PasswordField
from flask.ext.wtf import Required, Email, Length, EqualTo
from utils import RedirectForm


class SignupForm(RedirectForm):
    username = TextField('username', validators=[Required(), Length(min=5, max=30)])
    email = TextField('email', validators=[Required(), Email()])
    password = PasswordField('password', validators=[Required(), Length(min=8, max=30)])

    def validate_email(self, field):
        if current_app.db.get('select * from account where email=%s', field.data):
            raise ValueError("This email has been registed! choose another one!")

    def save(self):
        current_app.db.execute("""
           insert into account
           (email, username, password, created_at)
           values(%s, %s, %s, UTC_TIMESTAMP())
           """,
           self.email.data,
           self.username.data,
           generate_password_hash(self.password.data)
        )
        user = current_app.db.get('select * from account where email=%s', self.email.data)
        return user


class SigninForm(RedirectForm):
    """docstring for SigninForm"""
    email = TextField('email', validators=[Required(), Email()])
    password = PasswordField('password', validators=[Required(), Length(min=8, max=30)])

    def validate_email(self, field):
        user = current_app.db.get('select * from account where email=%s', field.data)
        if not user:
            raise ValueError('email or passord error!')
        if not user.get('is_active'):
            raise ValueError('account is not activated yet!')

    def validate_password(self, field):
        user = current_app.db.get('select * from account where email=%s', self.email.data)
        if not user:
            raise ValueError('email password error')
        if not check_password_hash(user['password'], field.data):
            raise ValueError('password error')
        self.user = user


class PasswordUpdateForm(RedirectForm):
    """docstring for PasswordUpdateForm"""
    current_password = PasswordField('Current password',
            validators=[Required()])
    new_password = PasswordField('New password',
            validators=[Required(), Length(min=8, max=30)])
    new_passsword_confirm = PasswordField('Confirm new password',
            validators=[Required(), EqualTo('new_password')])

    def validate_password(self, field):
        if not check_password_hash(g.user['password'], field.data):
            raise ValueError("Current password Error!")

    def save(self):
        current_app.db.execute('update account set password=%s where id=%s',
                generate_password_hash(self.password.data, g.user['id']))


class ResetMailForm(RedirectForm):
    """docstring for ResetMailForm"""
    email = TextField('email', validators=[Required(), Email()])

    def validate_email(self, field):
        if not current_app.db.get('select * from account where email=%s', field.data):
            raise ValueError('No account asociate with the email!!')


class PasswordResetForm(RedirectForm):
    """docstring for PasswordUpdateForm"""
    new_password = PasswordField('New password',
            validators=[Required(), Length(min=8, max=30)])
    new_passsword_confirm = PasswordField('Confirm new password',
            validators=[Required(), EqualTo('new_password')])

    def save(self, email):
        current_app.db.execute('update account set password=%s where email=%s',
                generate_password_hash(self.new_password.data), email)
