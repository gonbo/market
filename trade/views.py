#!/usr/bin/env python
# -*- coding: utf-8 -*-

from decimal import Decimal
from flask import Blueprint, render_template, current_app, g, \
        redirect, url_for, jsonify
from account.decorators import login_required
from .forms import BuyBitcoinForm, SellBitcoinForm
from tasks import order, BID, SELL, CANCEL_BID, CANCEL_SELL

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
        user = current_app.db.get('select * from account where id=%s', g.user['id'])
        if user.get('cny') > total:
            # appending to bid queue
            order.delay(BID, amount, price, user, total)
            return redirect(url_for('trade.orders'))
        else:
            return render_template('trade/buyBitcoin.html',
                    form=form,
                    errorMsg='Balance is not enough!')

    return render_template('trade/buyBitcoin.html', form=form)


@bp_trade.route('/cancel/bid/order/<int:order_id>', methods=['POST'])
@login_required
def cancel_bid_order(order_id):
    user = current_app.db.get('select * from account where id=%s', g.user['id'])
    order.delay(CANCEL_BID, user=user, order_id=order_id)
    return jsonify()


@bp_trade.route('/sell/bitcoin', methods=['GET', 'POST'])
@login_required
def sell_bitcoin():
    form = SellBitcoinForm()
    if form.validate_on_submit():
        user = current_app.db.get('select * from account where id=%s', g.user['id'])
        balance = user.get('btc')
        amount = Decimal(form.amount.data)
        if balance > amount:
            price = Decimal(form.price.data)
            order.delay(SELL, amount, price, user)
            return redirect(url_for('trade.orders'))
        else:
            return render_template('trade/sellBitcoin.html',
                    form=form,
                    errorMsg="Bitcoin is not enought!")

    return render_template('trade/sellBitcoin.html',form=form)


@bp_trade.route('/cancel/sell/order/<int:order_id>', methods=['POST'])
@login_required
def cancel_sell_order(order_id):
    user = current_app.db.get('select * from account where id=%s', g.user['id'])
    order(CANCEL_SELL, user=user, order_id=order_id)
    return jsonify()


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

@bp_trade.route('/market/depth')
def depth():
    """docstring for de"""
    return render_template('trade/depth.html')
