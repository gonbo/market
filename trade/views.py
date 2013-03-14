#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from decimal import Decimal
from flask import Blueprint, render_template, current_app, g, \
        redirect, url_for
from account.decorators import login_required
from .forms import BuyBitcoinForm, SellBitcoinForm
from tasks import bid, sell

COEFFICIENT = Decimal(10**12)
REVERSE_TIME_PARAM = Decimal('9999999999.999999')
PAGER = 10

bp_trade = Blueprint('trade', __name__)

@bp_trade.route('/buy/bitcoin', methods=['GET', 'POST'])
@login_required
def buy_bitcoin():
    form = BuyBitcoinForm()
    if form.validate_on_submit():
        amount = Decimal(form.amount.data)
        price = Decimal(form.price.data)
        total = amount * price
        balance = Decimal(current_app.redis.hget('account:%s'%g.user['id'], 'cny'))
        if balance > total:
            created_at = time.time()
            priority = Decimal(price)*COEFFICIENT + REVERSE_TIME_PARAM - Decimal(created_at)

            new_bid_order = {'uid': g.user['id'],
                    'amount': amount,
                    'price': price,
                    'created_at': created_at}

            system_next_bid_id = current_app.redis.hincrby('system', 'next_bid_id', 1)

            # atomically reduce cny balance and insert a new bid order
            pipe = current_app.redis.pipeline(transaction=True)
            pipe.hset('account:%s'%g.user['id'], 'cny', str(balance-total))
            pipe.hmset('bidOrder:%s'%system_next_bid_id, new_bid_order)
            pipe.zadd('bidQueue', system_next_bid_id, priority)
            pipe.lpush('account:%s:bids'%g.user['id'], system_next_bid_id)
            pipe.execute()

            bid.delay()

            return redirect(url_for('trade.orders'))
        else:
            return render_template('trade/buyBitcoin.html',
                    form=form,
                    errorMsg='Balance is not enough!')

    return render_template('trade/buyBitcoin.html', form=form)


@bp_trade.route('/sell/bitcoin', methods=['GET', 'POST'])
@login_required
def sell_bitcoin():
    form = SellBitcoinForm()
    if form.validate_on_submit():
        bitcoin_balance = Decimal(current_app.redis.hget('account:%s'%g.user['id'], 'btc'))
        amount = Decimal(form.amount.data)
        price = Decimal(form.price.data)
        if bitcoin_balance > amount:
            created_at = time.time()
            priority = Decimal(price)*COEFFICIENT + Decimal(created_at)

            new_ask_order = {'uid': g.user['id'],
                    'amount': amount,
                    'price': price,
                    'created_at': created_at}

            system_next_ask_id = current_app.redis.hincrby('system', 'next_ask_id', 1)

            # atomically reduce bitcoin balance and insert a new ask order
            pipe = current_app.redis.pipeline(transaction=True)
            pipe.hset('account:%s'%g.user['id'], 'btc', str(bitcoin_balance-amount))
            pipe.hmset('askOrder:%s'%system_next_ask_id, new_ask_order)
            pipe.zadd('askQueue', system_next_ask_id, priority)
            pipe.lpush('account:%s:asks'%g.user['id'], system_next_ask_id)
            pipe.execute()

            sell.delay()

            return redirect(url_for('trade.orders'))
        else:
            return render_template('trade/sellBitcoin.html',
                    form=form,
                    errorMsg="Bitcoin is not enought!")

    return render_template('trade/sellBitcoin.html',form=form)


@bp_trade.route('/orders')
@login_required
def orders():
    bids = []
    bid_order_ids = current_app.redis.lrange('account:%s:bids'%g.user['id'], 0, PAGER)
    for order_id in bid_order_ids:
        bids.append(current_app.redis.hgetall('bidOrder:%s'%order_id))

    asks = []
    ask_order_ids = current_app.redis.lrange('account:%s:asks'%g.user['id'], 0, PAGER)
    for ask_id in ask_order_ids:
        asks.append(current_app.redis.hgetall('askOrder:%s'%ask_id))

    return render_template('trade/orders.html', bids=bids, asks=asks)


@bp_trade.route('/trasactions')
@login_required
def transactions():
    transactions = []
    return render_template('trade/transactions.html', transactions=transactions)


@bp_trade.route('/market/history')
def market_history():
    return render_template('trade/marketHistory.html')
