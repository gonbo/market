#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, g, \
        redirect, url_for, current_app, abort
from .forms import SigninForm, SignupForm
from .helpers import login, logout
import mailing

bp_account = Blueprint('account', __name__)

@bp_account.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        new_user = form.save()
        mailing.send_awaiting_confirm_mail(new_user)
        return redirect(url_for('.signin'))

    return render_template('account/signup.html', form=form)


@bp_account.route('/signin', methods=['GET', 'POST'])
def signin():
    next_url = request.args.get('next', url_for('index'))

    if g.user:
        return redirect(next_url)

    form = SigninForm()
    if form.validate_on_submit():
        login(form.user)
        return redirect(next_url)

    return render_template('account/signin.html', form=form)


@bp_account.route('/signout')
def signout():
    next_url = request.args.get('next', url_for('index'))
    logout()
    return redirect(next_url)


@bp_account.route('/activate/<uid>')
def activate_user(uid):
    """
    Activate user funtion
    """
    active_code = request.args.get('code', None)
    found_user = current_app.redis.hgetall('account:%s' % uid)
    if not active_code or not found_user \
        or found_user.get('active_code') != active_code:
        return abort(404)

    if found_user.get('is_active') == 'False':
        current_app.redis.hset('account:%s' % uid, 'is_active', 'True')
        mailing.send_subscription_confirm_mail(found_user)
    else:
        # flash('accout is active!')
        pass

    return redirect(url_for('.signin'))
