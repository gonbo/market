#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template
from account.decorators import login_required

bp_fund = Blueprint('fund', __name__)

@bp_fund.route('/recharge/cny')
@login_required
def recharge_cny():
    return render_template('fund/rechargeCNY.html')


@bp_fund.route('/withdraw/cny')
@login_required
def withdraw_cny():
    return render_template('fund/withdrawCNY.html')


@bp_fund.route('/recharge/bitcoin')
@login_required
def recharge_bitcoin():
    return render_template('fund/rechargeBTC.html')


@bp_fund.route('/withdraw/bitcoin')
@login_required
def withdraw_bitcoin():
    return render_template('fund/withdrawBTC.html')
