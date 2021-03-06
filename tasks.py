import uuid
from celery import Celery
from celery.utils.log import get_task_logger
from fmail import Message
from utils import signer, mail, DEFAULT_MAIL_SENDER
from database import Connection
import settings

logger = get_task_logger(__name__)

celery = Celery('tasks', broker='redis://localhost:6379/0')

mysql = Connection(
        host=settings.MYSQL_HOST, database=settings.MYSQL_DATABASE,
        user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD,
        autocommit=False)


@celery.task
def exchange():
    """docstring for exchange"""
    try:
        lowest_ask_order = mysql.get('select * from ask_order_view limit 1')
        highest_bid_order = mysql.get('select * from bid_order_view limit 1')

        # debug
        if settings.CELERY_DEBUG:
            logger.info('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            logger.info(highest_bid_order)
            logger.info(lowest_ask_order)
            logger.info('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')

        while lowest_ask_order and highest_bid_order and \
            lowest_ask_order['price'] <= highest_bid_order['price'] and \
            lowest_ask_order['uid'] != highest_bid_order['uid']:

            logger.info('into while')
            delta = highest_bid_order['amount'] - lowest_ask_order['amount']
            if delta > 0:
                # do a transaction
                mysql.execute('''insert into transaction (amount, price, bid_order_id, ask_order_id,
                            bid_user_id, ask_user_id)
                            values(%s, %s, %s, %s, %s, %s)
                            ''',
                            lowest_ask_order['amount'],
                            lowest_ask_order['price'],
                            highest_bid_order['id'],
                            lowest_ask_order['id'],
                            highest_bid_order['uid'],
                            lowest_ask_order['uid'])

                # move ask order to history
                mysql.execute('''insert into user_ask_order_his (id, uid, amount, price, created_at)
                            values(%s, %s, %s, %s, %s)
                            ''',
                            lowest_ask_order['id'],
                            lowest_ask_order['uid'],
                            lowest_ask_order['amount'],
                            lowest_ask_order['price'],
                            lowest_ask_order['created_at'])
                mysql.execute('delete from user_ask_order where id=%s', lowest_ask_order['id'])

                # split bid order
                mysql.execute('''insert into user_bid_order_his (id, uid, amount, price,
                            strike_price, created_at)
                            values(%s, %s, %s, %s, %s, %s)
                            ''',
                            highest_bid_order['id'],
                            highest_bid_order['uid'],
                            lowest_ask_order['amount'],
                            highest_bid_order['price'],
                            lowest_ask_order['price'],
                            highest_bid_order['created_at'])
                mysql.execute('update user_bid_order set amount=%s where id=%s',
                            delta,
                            highest_bid_order['id'])

                # calculate volumn of this transaction, do exchange
                ask_user = mysql.get('select * from account where id=%s', lowest_ask_order['uid'])
                bid_user = mysql.get('select * from account where id=%s', highest_bid_order['uid'])
                mysql.execute('update account set cny=%s, frozen_btc=%s where id=%s',
                            ask_user['cny'] + lowest_ask_order['amount']*lowest_ask_order['price'],
                            ask_user['frozen_btc'] - lowest_ask_order['amount'],
                            lowest_ask_order['uid'])
                mysql.execute('update account set btc=%s, cny=%s, frozen_cny=%s where id=%s',
                            bid_user['btc'] + lowest_ask_order['amount'],
                            bid_user['cny'] + lowest_ask_order['amount']*(highest_bid_order['price']-lowest_ask_order['price']),
                            bid_user['frozen_cny'] - lowest_ask_order['amount']*highest_bid_order['price'],
                            highest_bid_order['uid'])
            elif delta < 0:
                # do a transaction,
                mysql.execute('''insert into transaction (amount, price, bid_order_id, ask_order_id,
                            bid_user_id, ask_user_id)
                            values(%s, %s, %s, %s, %s, %s)
                            ''',
                            highest_bid_order['amount'],
                            lowest_ask_order['price'],
                            highest_bid_order['id'],
                            lowest_ask_order['id'],
                            highest_bid_order['uid'],
                            lowest_ask_order['uid'])


                # move bid order to history
                mysql.execute('''insert into user_bid_order_his (id, uid, amount, price,
                            strike_price, created_at)
                            values(%s, %s, %s, %s, %s, %s)
                            ''',
                            highest_bid_order['id'],
                            highest_bid_order['uid'],
                            highest_bid_order['amount'],
                            highest_bid_order['price'],
                            lowest_ask_order['price'],
                            highest_bid_order['created_at'])
                mysql.execute('delete from user_bid_order where id=%s', highest_bid_order['id'])

                # split ask order
                mysql.execute('''insert into user_ask_order_his (id, uid, amount, price, created_at)
                            values(%s, %s, %s, %s, %s)
                            ''',
                            lowest_ask_order['id'],
                            lowest_ask_order['uid'],
                            highest_bid_order['amount'],
                            lowest_ask_order['price'],
                            lowest_ask_order['created_at'])
                mysql.execute('update user_ask_order set amount=%s where id=%s',
                            -delta,
                            lowest_ask_order['id'])

                # calculate volumn of this transaction, do exchange
                ask_user = mysql.get('select * from account where id=%s', lowest_ask_order['uid'])
                bid_user = mysql.get('select * from account where id=%s', highest_bid_order['uid'])
                mysql.execute('update account set cny=%s, frozen_btc=%s where id=%s',
                            ask_user['cny'] + highest_bid_order['amount']*lowest_ask_order['price'],
                            ask_user['frozen_btc'] - highest_bid_order['amount'],
                            lowest_ask_order['uid'])
                mysql.execute('update account set btc=%s, cny=%s, frozen_cny=%s where id=%s',
                            bid_user['btc'] + highest_bid_order['amount'],
                            bid_user['cny'] + highest_bid_order['amount']*(highest_bid_order['price']-lowest_ask_order['price']),
                            bid_user['frozen_cny'] - highest_bid_order['amount']*highest_bid_order['price'],
                            highest_bid_order['uid'])

            else:
                mysql.execute('''insert into transaction (amount, price, bid_order_id, ask_order_id,
                            bid_user_id, ask_user_id)
                            values(%s, %s, %s, %sd %s, %s)
                            ''',
                            lowest_ask_order['amount'],
                            lowest_ask_order['price'],
                            highest_bid_order['id'],
                            lowest_ask_order['id'],
                            highest_bid_order['uid'],
                            lowest_ask_order['uid'])
                # move both orders to history tables
                mysql.execute('''insert into user_bid_order_his (id, uid, amount, price,
                            strike_price, created_at)
                            values(%s, %s, %s, %s, %s, %s)
                            ''',
                            highest_bid_order['id'],
                            highest_bid_order['uid'],
                            highest_bid_order['amount'],
                            highest_bid_order['price'],
                            lowest_ask_order['price'],
                            highest_bid_order['created_at'])
                mysql.execute('delete from user_bid_order where id=%s', highest_bid_order['id'])
                mysql.execute('''insert into user_ask_order_his (id, uid, amount, price, created_at)
                            values(%s, %s, %s, %s, %s)
                            ''',
                            lowest_ask_order['id'],
                            lowest_ask_order['uid'],
                            lowest_ask_order['amount'],
                            lowest_ask_order['price'],
                            lowest_ask_order['created_at'])
                mysql.execute('delete from user_ask_order where id=%s', lowest_ask_order['id'])

                # calculate volumn of this transaction
                ask_user = mysql.get('select * from account where id=%s', lowest_ask_order['uid'])
                bid_user = mysql.get('select * from account where id=%s', highest_bid_order['uid'])
                mysql.execute('update account set cny=%s, frozen_btc=%s where id=%s',
                            ask_user['cny'] + lowest_ask_order['amount']*lowest_ask_order['price'],
                            ask_user['frozen_btc'] - lowest_ask_order['amount'],
                            lowest_ask_order['uid'])
                mysql.execute('update account set btc=%s, cny=%s, frozen_cny=%s where id=%s',
                            bid_user['btc'] + lowest_ask_order['amount'],
                            bid_user['cny'] + lowest_ask_order['amount']*(highest_bid_order['price']-lowest_ask_order['price']),
                            bid_user['frozen_cny'] - lowest_ask_order['amount']*highest_bid_order['price'],
                            highest_bid_order['uid'])

            lowest_ask_order = mysql.get('select * from ask_order_view limit 1')
            highest_bid_order = mysql.get('select * from bid_order_view limit 1')

            # debug
            if settings.CELERY_DEBUG:
                logger.info('------------------------------------------------------------')
                logger.info(highest_bid_order)
                logger.info(lowest_ask_order)
                logger.info('------------------------------------------------------------')

        mysql.commit()
    except Exception, e:
        logger.error(e)
        mysql.rollback()


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
                    reset_code)

    mysql.commit()
    mail.send(mail_to_be_send)
