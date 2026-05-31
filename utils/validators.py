import re

def validate_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters"
    return None
