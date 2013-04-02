#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
from flask import Blueprint, render_template, current_app, g, jsonify
from account.decorators import login_required
from .forms import TradeForm
from tasks import exchange

PAGER = 10

bp_trade = Blueprint('trade', __name__)

@bp_trade.route('/')
@login_required
def trade():
    account = current_app.db.get('select * from account where id=%s', g.user['id'])
    bids = current_app.db.query('select * from user_bid_order where uid=%s order by created_at desc',
            g.user['id'])
    asks = current_app.db.query('select * from user_ask_order where uid=%s order by created_at desc',
            g.user['id'])

    return render_template('trade/trade.html',
            account=account,
            bids=bids,
            asks=asks,
            bidForm=TradeForm(),
            askForm=TradeForm())


@bp_trade.route('/buy', methods=['POST'])
@login_required
def buy():
    form = TradeForm()
    if form.validate_on_submit():
        amount = form.amount.data
        price = form.price.data

        account = current_app.db.get('select * from account where id=%s', g.user['id'])

        total = amount * price
        if account.get('cny') > total:
            current_app.db.execute('update account set cny=%s, frozen_cny=%s where id=%s',
                    account['cny'] -total,
                    account['frozen_cny'] + total,
                    g.user['id'])

            current_app.db.execute('insert into user_bid_order (id, uid, amount, price) values(%s, %s, %s, %s)',
                    uuid.uuid4().int, g.user['id'], amount, price)

            exchange.delay()
            return jsonify(success=1, result={'amount': float(amount), 'price': float(price)})

        return jsonify(success=0, error={'msg': 'No enough fund.'})

    return jsonify(success=0, error={'msg': form.errors})


@bp_trade.route('/sell', methods=['POST'])
@login_required
def sell():
    form = TradeForm()
    if form.validate_on_submit():
        amount = form.amount.data
        price = form.price.data

        account = current_app.db.get('select * from account where id=%s', g.user['id'])

        if account.get('btc') > amount:
            current_app.db.execute('update account set btc=%s, frozen_btc=%s where id=%s',
                    account['btc'] - amount,
                    account['frozen_btc'] + amount,
                    g.user['id'])

            current_app.db.execute('insert into user_ask_order (id, uid, amount, price) values(%s, %s, %s, %s)',
                    uuid.uuid4().int, g.user['id'], amount, price)

            exchange.delay()
            return jsonify(success=1, result={'amount': float(amount), 'price': float(price)})

        return jsonify(success=0, error={'msg': 'No enough btc.'})

    return jsonify(success=0, error={'msg': form.errors})


@bp_trade.route('/orders')
@login_required
def orders():
    bids= current_app.db.query('select * from user_bid_order where uid=%s order by created_at desc',
            g.user['id'])
    asks = current_app.db.query('select * from user_ask_order where uid=%s order by created_at desc',
            g.user['id'])
    return render_template('trade/orders.html', bids=bids, asks=asks)


@bp_trade.route('/trasactions')
@login_required
def transactions():
    transactions = current_app.db.query('''select * from transaction
        where bid_user_id=%s or ask_order_id =%s order by done_at''',
        g.user['id'], g.user['id'])

    return render_template('trade/transactions.html', transactions=transactions)


@bp_trade.route('/market/history')
def market_history():
    return render_template('trade/marketHistory.html')


@bp_trade.route('/market/depth')
def depth():
    """docstring for de"""
    return render_template('trade/depth.html')
