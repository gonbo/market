#!/usr/bin/env python

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_NUM = 3
SECRET_KEY = '\x1f\x08<\\\xccP\xf1\xae\x8cjr&E\x00\x0c=.V\xa4\xc7\xff\\\xae5'

# flask-mail configure
MAIL_SERVER='smtp.163.com'
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME = 'btcmarket@163.com'
MAIL_PASSWORD = 'btcpass'
DEFAULT_MAIL_SENDER='btcmarket@163.com'
DEFAULT_BROKER = 'redis://localhost:6379/0'

MYSQL_HOST = "localhost"
MYSQL_DATABASE = "btc"
MYSQL_USER = "btc"
MYSQL_PASSWORD = "btcpass"
