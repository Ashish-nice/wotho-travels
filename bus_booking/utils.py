import pyotp
from datetime import datetime, timedelta
from django.conf import settings
from mailjet_rest import Client

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
        # Setup Mailjet client
        mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET), version='v3.1')
        
        # Prepare data for Mailjet API
        data = {
            'Messages': [
                {
                    'From': {
                        'Email': settings.EMAIL_HOST_USER,
                        'Name': 'Wotho Travels'
                    },
                    'To': [
                        {
                            'Email': email,
                            'Name': 'Traveler'
                        }
                    ],
                    'Subject': subject,
                    'TextPart': message_text,
                }
            ]
        }
        
        # Send email using Mailjet
        result = mailjet.send.create(data=data)
        
        if result.status_code == 200:
            print(f"OTP email sent successfully to {email}")
            return True
        else:
            print(f"Error sending email via Mailjet: {result.reason}")
            return False
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
