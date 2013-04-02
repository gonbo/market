#!/usr/bin/env python

import uuid
from flask import Blueprint, current_app, jsonify, g
from account.decorators import login_required
from .forms import APITradeForm, APICancelForm, ACTION_TYPE_CHOICES
from tasks import exchange

bp_trade = Blueprint('trade', __name__)

bp_api = Blueprint('api', __name__)

@bp_api.route('/trade', methods=['POST'])
@login_required
def trade():
    form = APITradeForm()
    if form.validate_on_submit():
        action_type = form.action_type.data
        amount = form.amount.data
        price = form.price.data

        account = current_app.db.get('select * from account where id=%s', g.user['id'])

        if action_type == ACTION_TYPE_CHOICES[0]:
            total = amount * price
            if account.get('cny') > total:
                current_app.db.execute('update account set cny=%s, frozen_cny=%s where id=%s',
                        account['cny'] -total,
                        account['frozen_cny'] + total,
                        g.user['id'])

                current_app.db.execute('insert into user_bid_order (id, uid, amount, price) values(%s, %s, %s, %s)',
                        uuid.uuid4().int, g.user['id'], amount, price)

                exchange.delay()
                return jsonify(success=1, result={'amount': amount, 'price': price})

            return jsonify(success=0, error={'msg': 'No enough fund.'})
        elif action_type == ACTION_TYPE_CHOICES[1]:
            if account.get('btc') > amount:
                current_app.db.execute('update account set btc=%s, frozen_btc=%s where id=%s',
                        account['btc'] - amount,
                        account['frozen_btc'] + amount,
                        g.user['id'])

                current_app.db.execute('insert into user_ask_order (id, uid, amount, price) values(%s, %s, %s, %s)',
                        uuid.uuid4().int, g.user['id'], amount, price)

                exchange.delay()
                return jsonify(success=1, result={'amount': amount, 'price': price})

            return jsonify(success=0, error={'msg': 'No enough btc.'})

    return jsonify(success=0, error={'msg': form.errors})


@bp_api.route('/cancel_order', methods=['POST'])
@login_required
def cancel_order():
    form = APICancelForm()
    if form.validate_on_submit():
        if form.order_type.data == ACTION_TYPE_CHOICES[0]:
            current_app.db.execute('delete from user_bid_order where id=%s and uid=%s',
                    form.order_id.data, g.user['id'])
            return jsonify(success=1, result={'msg': 'done'})
        elif form.order_type.data == ACTION_TYPE_CHOICES[1]:
            current_app.db.execute('delete from user_ask_order where id=%s and uid=%s',
                    form.order_id.data, g.user['id'])
            return jsonify(success=1, result={'msg': 'done'})

    return jsonify(success=0, error={'msg': form.errors})
