#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
from flask import Flask, g, render_template
from flask_mail import Mail
from account.helpers import get_current_user
from account.views import bp_account
from trade.views import bp_trade
from fund.views import bp_fund

app = Flask(__name__)
app.config.from_object('settings')
app.config.update(
        DEBUG=True,
        #EMAIL SETTINGS
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=465,
        MAIL_USE_SSL=True,
        MAIL_USERNAME = 'emyris.fan@gmail.com',
        MAIL_PASSWORD = 'Ilmctbsbe,./122168'
        )

app.mail = Mail(app)
app.redis = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'], db=3)

app.register_blueprint(bp_account, url_prefix="/account")
app.register_blueprint(bp_trade, url_prefix="/trade")
app.register_blueprint(bp_fund, url_prefix="/fund")

@app.before_request
def before_request():
    g.user = get_current_user()



@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run('0.0.0.0', port=7777, debug=True)
