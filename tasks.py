import uuid
import time
from decimal import Decimal
from celery import Celery
from fmail import Message
from utils import signer, mail, redis_db, DEFAULT_MAIL_SENDER
from database import Connection
import settings

COEFFICIENT = Decimal(10**12)
REVERSE_TIME_PARAM = Decimal('9999999999.999999')
BID = 0
SELL = 1
CANCEL_BID = 2
CANCEL_SELL = 3

BID_LUA_SCRIPT = """
    local uid = ARGV[1]
    local amount = tonumber(ARGV[2])
    local price = tonumber(ARGV[3])
    local balance = tonumber(ARGV[4])
    local total = tonumber(ARGV[5])
    local created_at = tonumber(ARGV[6])
    local priority = tonumber(ARGV[7])

    local next_bid_id = redis.call('hincrby', 'system', 'next_bid_id', 1)
    redis.call('hset', 'account:' .. uid, 'cny', balance-total)
    redis.call('hmset', 'bidOrder:' .. next_bid_id, 'uid', uid, 'amount', amount, 'price', price, 'created_at', created_at, 'type', BID)
    redis.call('zadd', 'bidQueue', priority, next_bid_id)
    redis.call('lpush', 'account:' .. uid .. ":bids", next_bid_id)
    return true
"""

SELL_LUA_SCRIPT = """
    local uid = ARGV[1]
    local amount = tonumber(ARGV[2])
    local price = tonumber(ARGV[3])
    local balance = tonumber(ARGV[4])
    local created_at = tonumber(ARGV[5])
    local priority = tonumber(ARGV[6])

    local next_ask_id = redis.call('hincrby', 'system', 'next_ask_id', 1)
    redis.call('hset', 'account:' .. uid, 'cny', balance-amount)
    redis.call('hmset', 'askOrder:' .. next_ask_id, 'uid', uid, 'amount', amount, 'price', price, 'created_at', created_at, 'type', SELL)
    redis.call('zadd', 'askQueue', priority, next_ask_id)
    redis.call('lpush', 'account:' .. uid .. ":asks", next_ask_id)
    return true
"""

CANCEL_BID_LUA_SCRIPT = """
    local uid = ARGV[1]
    local order_id = ARGV[2]
"""

CANCEL_SELL_LUA_SCRIPT = """
    local uid = ARGV[1]
    local order_id = ARGV[2]
"""

# Remove all the scripts from the script cache.
redis_db.script_flush()
# register actions
bid = redis_db.register_script(BID_LUA_SCRIPT)
sell = redis_db.register_script(SELL_LUA_SCRIPT)
cancel_bid = redis_db.register_script(CANCEL_BID_LUA_SCRIPT)
cancel_sell = redis_db.register_script(CANCEL_SELL_LUA_SCRIPT)

celery = Celery('tasks', broker='redis://localhost:6379/0')
mysql = Connection(
        host=settings.MYSQL_HOST, database=settings.MYSQL_DATABASE,
        user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD)

@celery.task
def order(action_type, uid, amount=None, price=None, balance=None,
        total=None, order_id=None):
    if action_type == BID:
        created_at = time.time()
        priority = Decimal(price)*COEFFICIENT + REVERSE_TIME_PARAM - Decimal(created_at)
        args = [uid, amount, price, balance, total, created_at, priority]
        bid(args=args)
    elif action_type == SELL:
        created_at = time.time()
        priority = Decimal(price)*COEFFICIENT + Decimal(created_at)
        args = [uid, amount, price, balance, created_at, priority]
        sell(args=args)
    elif action_type == CANCEL_BID:
        cancel_bid(uid, order_id)
    elif action_type == CANCEL_SELL:
        cancel_sell(uid, order_id)


@celery.task
def send_register_confirm_mail(user, confirm_url):
    """
    Send the awaiting for confirmation mail to the user.
    """
    subject = "We're waiting for your confirmation!"
    mail_to_be_send = Message(subject=subject, sender=DEFAULT_MAIL_SENDER, recipients=[user['email']])
    signature = signer.sign(str(user['id']))
    confirmation_url = confirm_url + "?sign=" + signature
    mail_to_be_send.body = "Dear %s, click the following url to confirm: %s" % \
            (user['email'], confirmation_url)
    mail.send(mail_to_be_send)


@celery.task
def send_subscription_confirm_mail(user):
    subject = "Welcome!!"
    mail_to_be_send = Message(subject=subject, sender=DEFAULT_MAIL_SENDER, recipients=[user['email']])
    mail_to_be_send.body = "Congratulaition!"
    mail.send(mail_to_be_send)


@celery.task
def send_reset_password_mail(email, reset_url):
    """
    Send a reset mail to user, allow the user to reset password.
    """
    subject = "Reset Password"
    mail_to_be_send = Message(subject=subject, sender=DEFAULT_MAIL_SENDER, recipients=[email])
    reset_code = uuid.uuid4()
    reset_url =  reset_url + "?code=" + str(reset_code)
    mail_to_be_send.body = "Dear %s, click the following url to reset your password:%s" % \
            (email, reset_url)

    mysql.execute("""insert into reset (email, reset_code)
                    values(%s, %s)
                    """,
                    email,
                    reset_code
                    )
    mail.send(mail_to_be_send)
