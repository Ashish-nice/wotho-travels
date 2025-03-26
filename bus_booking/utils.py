import pyotp
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32(), interval=300)
    return totp.now()

def send_booking_otp(email, otp):
    subject = 'Verify your booking'
    message = f'''
    Your OTP for booking verification is: {otp}
    
    This OTP will expire in 5 minutes.
    
    If you didn't request this, please ignore this email.
    '''
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    