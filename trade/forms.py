from decimal import Decimal
from flask.ext.wtf import Form
from flask.ext.wtf import DecimalField
from flask.ext.wtf import Required, NumberRange


class BuyBitcoinForm(Form):
    amount = DecimalField('amount', validators=[Required(),NumberRange(min=Decimal('0.00000001'))])
    price = DecimalField('price', validators=[Required(), NumberRange(min=Decimal('0.01'))])


class SellBitcoinForm(Form):
    amount = DecimalField('amount', validators=[Required(),NumberRange(min=Decimal('0.00000001'))])
    price = DecimalField('price', validators=[Required(), NumberRange(min=Decimal('0.01'))])
