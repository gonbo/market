from decimal import Decimal
from flask.ext.wtf import Form
from flask.ext.wtf import DecimalField
from flask.ext.wtf import Required, NumberRange, SelectField, FloatField

ACTION_TYPE_CHOICES = ['buy', 'sell']

class APITradeForm(Form):
    action_type = SelectField('type', validators=[Required()], choices=ACTION_TYPE_CHOICES)
    amount = DecimalField('amount', validators=[Required(),NumberRange(min=Decimal('0.00000001'))])
    price = DecimalField('price', validators=[Required(), NumberRange(min=Decimal('0.01'))])

    def validate_csrf_token(self, field):
        """
        disable csrf protection
        """
        pass


class APICancelForm(Form):
    order_id = FloatField('order_id', validators=[Required()])
    order_type = SelectField('type', validators=[Required()], choices=ACTION_TYPE_CHOICES)

    def validate_csrf_token(self, field):
        """
        disable csrf protection
        """
        pass
