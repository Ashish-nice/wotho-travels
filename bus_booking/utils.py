import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from django.conf import settings

def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32(), interval=300)
    return totp.now()

def send_booking_otp(email, otp):
    subject = 'Verify your booking'
    message_text = f'''
    Your OTP for booking verification is: {otp}
    
    This OTP will expire in 5 minutes.
    
    If you didn't request this, please ignore this email.
    '''
    
    try:
        # Create a multipart message
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message_text, 'plain'))
        
        # Connect directly to Gmail's SSL port using with statement for proper cleanup
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
            # Send email
            server.send_message(msg)
        
        print(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
