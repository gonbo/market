import redis
from itsdangerous import Signer
from fmail import Mail
import settings

DEFAULT_MAIL_SENDER =  settings.DEFAULT_MAIL_SENDER

mail = Mail("settings")

signer = Signer(settings.SECRET_KEY)

redis_db = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_NUM)
