#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
from flask import Flask, g, render_template, request, Response, current_app
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin
from account.helpers import get_current_user
from account.views import bp_account
from trade.views import bp_trade
from fund.views import bp_fund
from trade.forms import BuyBitcoinForm, SellBitcoinForm

app = Flask(__name__)
app.config.from_object('settings')

app.redis = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_NUM'])

app.register_blueprint(bp_account, url_prefix="/account")
app.register_blueprint(bp_trade, url_prefix="/trade")
app.register_blueprint(bp_fund, url_prefix="/fund")


@app.before_request
def before_request():
    g.user = get_current_user()


class ChatNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    nicknames = []

    def initialize(self):
        self.logger = app.logger
        self.session['nickname'] = 'michael'
        self.log("Socketio session started")

    def log(self, message):
        self.logger.info("[{0}] {1}".format(self.socket.sessid, message))

    def on_join(self, room):
        self.room = room
        self.join(room)
        return True

    def on_nickname(self, nickname):
        self.log('Nickname: {0}'.format(nickname))
        self.nicknames.append(nickname)
        self.session['nickname'] = nickname
        self.broadcast_event('announcement', '%s has connected' % nickname)
        self.broadcast_event('nicknames', self.nicknames)
        return True, nickname

    def recv_disconnect(self):
        # Remove nickname from the list.
        self.log('Disconnected')
        nickname = self.session['nickname']
        self.nicknames.remove(nickname)
        self.broadcast_event('announcement', '%s has disconnected' % nickname)
        self.broadcast_event('nicknames', self.nicknames)
        self.disconnect(silent=True)
        return True

    def on_user_message(self, msg):
        self.log('User message: {0}'.format(msg))
        self.emit_to_room(self.room, 'msg_to_room',
            self.session['nickname'], msg)
        return True


@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        socketio_manage(request.environ, {'/chat': ChatNamespace}, request)
    except:
        app.logger.error("Exception while handling socketio connection",
                         exc_info=True)
    return Response()


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
                transactions=transactions,
                buy_form=BuyBitcoinForm(),
                sell_form=SellBitcoinForm())

    return render_template('index.html',
            bids=bids,
            asks=asks,
            transactions=transactions)


if __name__ == '__main__':
    app.run('0.0.0.0', 7777, True)
