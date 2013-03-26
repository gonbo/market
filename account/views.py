#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, g, \
        redirect, url_for, current_app, abort, session, flash
from itsdangerous import BadSignature
from .forms import SigninForm, SignupForm, PasswordUpdateForm, \
        ResetMailForm, PasswordResetForm
from .helpers import login, logout
from .decorators import login_required
from tasks import send_register_confirm_mail, send_subscription_confirm_mail, \
            send_reset_password_mail
from utils import signer

bp_account = Blueprint('account', __name__)


@bp_account.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        new_user = form.save()
        # mailing.send_awaiting_confirm_mail(new_user)
        confirm_url = url_for('account.activate_user', _external=True)
        send_register_confirm_mail.delay(new_user, confirm_url)
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


@bp_account.route('/activate')
def activate_user():
    """
    Activate user funtion
    """
    active_code = request.args.get('sign', None)
    if active_code:
        try:
            uid = signer.unsign(active_code)
            user = current_app.db.get('select * from account where id=%s', uid)
            if user and user.get('is_active') == 0:
                current_app.db.execute('update account set is_active=1 where id=%s', uid)
                send_subscription_confirm_mail.delay(user)
            elif user:
                flash('User already activated!!')
        except BadSignature, e:
            current_app.logger.warning(e)
            abort(404)

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
        reset_url = url_for('account.reset_password', _external=True)
        send_reset_password_mail.delay(form.email.data,reset_url)
        return redirect(url_for('index'))
    return render_template('account/sendResetMail.html', form=form)


@bp_account.route('/reset/password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        reset_code = request.args.get('code')
        if reset_code:
            item =  current_app.db.get('select * from reset where reset_code=%s', reset_code)
            if item:
                session['email'] = item.get('email')
                session['reset_code'] = reset_code
            else:
                abort(404)
        return render_template('account/resetPassword.html', form=PasswordResetForm())
    else:
        if not session.get('email'):
            return abort(404)

        form = PasswordResetForm()
        if form.validate_on_submit():
            form.save(session.get('email'))
            current_app.db.execute('delete from reset where reset_code=%s',
                    session.get('reset_code'))
            session.pop('email', None)
            session.pop('reset_code', None)
            return redirect(url_for('.signin'))
        return render_template('account/resetPassword.html', form=form)
