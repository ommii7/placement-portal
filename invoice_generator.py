import os
from datetime import datetime

class InvoiceGenerator:
    def __init__(self):
        os.makedirs("static/invoices", exist_ok=True)
    def generate_invoice(self, user, subscription, transaction):
        path = f"static/invoices/invoice_{transaction.id}.html"
        with open(path, 'w') as f:
            f.write(f"<html><body><h1>Invoice</h1><p>User: {user.email}</p><p>Amount: {subscription.amount}</p></body></html>")
        return path