import time
import uuid
from flask import session, current_app, request

def get_current_user():
    token = request.args.get('token', session.get('token', None))
    if not token:
        return None

    user_session = current_app.redis.hgetall('session:%s'%token)
    if not user_session:
        return None

    user = current_app.redis.hgetall('account:%s'%user_session['uid'])
    if user.get('token') != user_session.get('token'):
        return None

    return user


def login(user):
    if not user:
        return None

    new_token = uuid.uuid4()
    session['token'] = new_token
    current_app.redis.hmset('session:%s'%new_token,
            {'uid': user['id'], 'token': new_token, 'created_at': time.time()})
    # update user token everytime when login
    current_app.redis.hset('account:%s' % user['id'], 'token', new_token)
    return user


def logout():
    session.pop('token', None)

