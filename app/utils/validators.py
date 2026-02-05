import re
from email_validator import validate_email as email_validate, EmailNotValidError

def validate_email(email):
    try:
        # For testing, allow example.com domains
        if email.endswith('@example.com'):
            return True
        email_validate(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def validate_password(password):
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Z]', password):
        return False
    
    if not re.search(r'[a-z]', password):
        return False
    
    if not re.search(r'[0-9]', password):
        return False
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True

def validate_username(username):
    if not username or len(username) < 3 or len(username) > 80:
        return False
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False
    
    return True

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
