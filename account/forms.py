#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import time
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, g
from flask.ext.wtf import Form
from flask.ext.wtf import TextField, PasswordField
from flask.ext.wtf import Required, Email, Length, EqualTo


class SignupForm(Form):
    username = TextField('username', validators=[Required(), Length(min=5, max=30)])
    email = TextField('email', validators=[Required(), Email()])
    password = PasswordField('password', validators=[Required(), Length(min=8, max=30)])

    def validate_email(self, field):
        if current_app.redis.exists('email:%s:uid' % field.data):
            raise ValueError("This email has been registed! choose another one!")

    def save(self):
        uid = current_app.redis.hincrby('system', 'next_uid', 1)
        token = uuid.uuid4().get_hex()

        user = {'id': uid,
                'username': self.username.data,
                'password': generate_password_hash(self.password.data),
                'email': self.email.data,
                'token': token,
                'created_at': time.time(),
                'is_active': False,
                'btc': str(Decimal('0.00000000')),
                'cny': str(Decimal('0.00')),
                'frozen_cny': str(Decimal('0.00')),
                'frozen_btc': str(Decimal('0.000000000'))
                }
        current_app.redis.set('email:%s:uid'%self.email.data, uid)
        current_app.redis.hmset('account:%s'%uid, user)
        return user


class SigninForm(Form):
    """docstring for SigninForm"""
    email = TextField('email', validators=[Required(), Email()])
    password = PasswordField('password', validators=[Required(), Length(min=8, max=30)])

    def validate_email(self, field):
        uid = current_app.redis.get('email:%s:uid' % field.data)
        if not uid:
            raise ValueError('email or passord error!')
        if current_app.redis.hget('account:%s' % uid, 'is_active') == 'False':
            raise ValueError('account is not activated yet!')

    def validate_password(self, field):
        uid = current_app.redis.get('email:%s:uid' % self.email.data)
        if not uid:
            raise ValueError('email or password error')

        user = current_app.redis.hgetall('account:%s'%uid)
        if not check_password_hash(user['password'], field.data):
            raise ValueError('email or password error')

        update_info = {'token': uuid.uuid4().get_hex(), 'last_login': time.time()}
        current_app.redis.hmset('account:%s'%uid, update_info)
        # for login()
        user.update(update_info)
        self.user = user

class PasswordUpdateForm(Form):
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
        current_app.redis.hset('user:%s'%g.user['id'], 'password',
                generate_password_hash(self.new_password.data))

class ResetMailForm(Form):
    """docstring for ResetMailForm"""
    email = TextField('email', validators=[Required(), Email()])

    def validate_email(self, field):
        if not current_app.redis.exists('email:%s:uid' % field.data):
            raise ValueError('No account asociate with the email!!')


class PasswordResetForm(Form):
    """docstring for PasswordUpdateForm"""
    new_password = PasswordField('New password',
            validators=[Required(), Length(min=8, max=30)])
    new_passsword_confirm = PasswordField('Confirm new password',
            validators=[Required(), EqualTo('new_password')])

    def save(self, email):
        uid  = current_app.redis.get('email:%s:uid' % email)
        current_app.redis.hset('account:%s' % uid, 'password',
                generate_password_hash(self.new_password.data))
