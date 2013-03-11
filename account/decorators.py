import functools
from flask import redirect, url_for, request, g

def login_required(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        if g.user:
            return method(*args, **kwargs)
        else:
            url = url_for('account.signin')
            if '?' not in url:
                url += '?next=' + request.url
            return redirect(url)
    return wrapper
