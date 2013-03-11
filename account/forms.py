#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import time
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask.ext.wtf import Form
from flask.ext.wtf import TextField, PasswordField
from flask.ext.wtf import Required, Email, Length


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
                'rmb': str(Decimal('0.00'))
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
