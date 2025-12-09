from flask_mail import Mail, Message
from flask import current_app
import threading

def send_async_email(app, msg):
    with app.app_context():
        try:
            # Import mail here to avoid circular imports if initialized in app
            # But better to access via current_app if setup correctly
            mail = current_app.extensions.get('mail')
            if mail:
                mail.send(msg)
                print(f"Sent email to {msg.recipients}")
        except Exception as e:
            print(f"Failed to send email: {e}")

def send_email(to, subject, body):
    """
    Sends an email. If MAIL_SERVER is not configured, prints to console.
    """
    app = current_app._get_current_object()
    
    # Check if mail is configured
    if not app.config.get('MAIL_SERVER'):
        print("-------------------------------------------------")
        print(f"EMAIL SIMULATION (No SMTP Configured)")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print("-------------------------------------------------")
        return

    msg = Message(subject, recipients=[to])
    msg.body = body
    
    # Send asynchronously to avoid blocking
    thr = threading.Thread(target=send_async_email, args=(app, msg))
    thr.start()

def check_and_alert_limit(user, resource_type, usage, limit):
    """
    Checks if usage exceeds limit and sends alert if needed.
    """
    if limit > 0 and usage > limit:
        percentage = (usage / limit) * 100
        subject = f"⚠️ Limit Exceeded: {resource_type.capitalize()} Usage Alert"
        body = f"""Hello {user.username},

Your {resource_type} usage has exceeded your monthly limit!

Current Usage: {usage}
Monthly Limit: {limit}
Status: {percentage:.1f}%

Please consider conserving resources to stay within your budget.

Regards,
Smart Resource Tracker
"""
        send_email(user.email, subject, body)
