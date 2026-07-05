"""Identity validation (PoC). Two lightweight steps, like a real telco line:
  1. sign in with email + shared demo password
  2. verify identity with the last 4 digits on file (customer['last4_id'])
Only after both does the customer reach the chat."""
from . import data_store, config


def check_login(email, password):
    cust = data_store.find_customer_by_email(email)
    if cust and password == config.DEMO_PASSWORD:
        return cust
    return None


def verify_identity(cust, last4):
    return bool(cust) and (last4 or "").strip() == str(cust.get("last4_id"))


def demo_directory():
    """Small helper so the login screen can show valid demo logins."""
    return [
        {"email": c["email"], "name": f"{c['first_name']} {c['last_name']}",
         "last4": c["last4_id"], "tier": c["loyalty_tier"]}
        for c in data_store.all_customers().values()
    ]
