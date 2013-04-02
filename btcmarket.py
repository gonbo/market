#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
from flask import Flask, g, render_template, current_app
from account.helpers import get_current_user
from account.views import bp_account
from trade.views import bp_trade
from fund.views import bp_fund
from api.views import bp_api
import database

app = Flask(__name__)
app.config.from_object('settings')

app.redis = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_NUM'])

app.db = database.Connection(
        host=app.config['MYSQL_HOST'], database=app.config['MYSQL_DATABASE'],
        user=app.config['MYSQL_USER'], password=app.config['MYSQL_PASSWORD'])

app.register_blueprint(bp_account, url_prefix="/account")
app.register_blueprint(bp_trade, url_prefix="/trade")
app.register_blueprint(bp_fund, url_prefix="/fund")
app.register_blueprint(bp_api, url_prefix="/api")


@app.before_request
def before_request():
    g.user = get_current_user()

@app.route('/')
def index():
    ask_ids = current_app.redis.zrange('askQueue', 0, 20)
    asks = []
    for ask_id in ask_ids:
        current_app.logger.info(ask_id)
        asks.append(current_app.redis.hgetall('askOrder:%s'%ask_id))

    bid_ids = current_app.redis.zrange('bidQueue', 0, 20)
    bids = []
    for bid_id in bid_ids:
        current_app.logger.info(bid_id)
        bids.append(current_app.redis.hgetall('bidOrder:%s'%bid_id))

    transaction_ids = current_app.redis.zrange('transactions', 0, 20)
    transactions = []
    for tid in transaction_ids:
        transactions.append(current_app.redis.hgetall('transaction:%s'%tid))

    if g.user:
        ask_order_ids = current_app.redis.lrange('account:%s:asks'%g.user['id'], 0, 20)
        user_orders = []
        for ask_order_id in ask_order_ids:
            user_orders.append(current_app.redis.hgetall('askOrder:%s'%ask_order_id))
        bid_order_ids = current_app.redis.lrange('account:%s:asks'%g.user['id'], 0, 20)
        for bid_order_id in bid_order_ids:
            user_orders.append(current_app.redis.hgetall('bidOrder:%s'%bid_order_id))

        return render_template('index.html',
                user_orders=user_orders,
                bids=bids,
                asks=asks,
                transactions=transactions)

    return render_template('index.html',
            bids=bids,
            asks=asks,
            transactions=transactions)


if __name__ == '__main__':
    app.run('0.0.0.0', 5000, True)
