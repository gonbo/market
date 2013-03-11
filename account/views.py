#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, g, \
        redirect, url_for, current_app, abort, session
from .forms import SigninForm, SignupForm, PasswordUpdateForm, \
        ResetMailForm, PasswordResetForm
from .helpers import login, logout
from .decorators import login_required
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


@bp_account.route('/change/password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordUpdateForm()
    if form.validate_on_submit():
        form.save()
        return redirect(url_for('index'))
    return render_template('account/changePassword.html', form=form)


@bp_account.route('/send/resetmail', methods=['GET', 'POST'])
def send_resetmail():
    form = ResetMailForm()
    if form.validate_on_submit():
        mailing.send_reset_password_mail(form.email.data)
        return redirect(url_for('index'))
    return render_template('account/sendResetMail.html', form=form)


@bp_account.route('/reset/password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        if not request.args.get('code'):
            return abort(404)
        reset_code = request.args.get('code')
        email = current_app.redis.get('reset:%s:email' % reset_code)
        if not email:
            return abort(404)
        session['email'] = email;
        session['reset_code'] = reset_code
        return render_template('account/resetPassword.html', form=PasswordResetForm())
    elif request.method == 'POST':
        if not session.get('email'):
            return abort(404)

        form = PasswordResetForm()
        if form.validate_on_submit():
            form.save(session.get('email'))
            current_app.redis.delete('reset:%s:email' % session.get('reset_code'))
            session.pop('email', None)
            session.pop('reset_code', None)
            return redirect(url_for('.signin'))
        return render_template('account/resetPassword.html', form=form)
