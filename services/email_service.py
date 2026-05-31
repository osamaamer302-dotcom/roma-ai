from flask_mail import Mail, Message
mail = Mail()

def send_verification_email(email, name, token):
    try:
        msg = Message("Verify your Roma AI account", recipients=[email])
        msg.html = f"""<h2>Welcome to Roma AI!</h2>
        <p>Click to verify: <a href="http://localhost:5000/api/auth/verify-email?token={token}">Verify Email</a></p>"""
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")

def send_password_reset_email(email, name, token):
    try:
        msg = Message("Reset your Roma AI password", recipients=[email])
        msg.html = f"""<h2>Password Reset</h2>
        <p>Click to reset: <a href="http://localhost:5000/api/auth/reset-password?token={token}">Reset Password</a></p>"""
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")

def send_campaign_email(email, name, subject, body_html):
    try:
        msg = Message(subject, recipients=[email])
        msg.html = body_html.replace("{name}", name or "there")
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")
