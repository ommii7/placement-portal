import secrets
from datetime import datetime

class PaymentHandler:
    def process_payment(self, amount, email):
        return {'success': True, 'payment_id': f"PAY_{secrets.token_hex(8).upper()}"}