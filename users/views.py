from django.shortcuts import render,redirect
from .forms import SignUpForm, UserUpdateForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.contrib.auth import get_user_model
from threading import Thread
from .tokens import account_activation_token
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

User = get_user_model()

def send_verification_email(user, request):
    current_site = get_current_site(request)
    subject = 'Activate Your Account'
    domain = getattr(current_site, 'domain', 'wotho-travels.xtasi.me')
    
    # Create HTML message content
    html_content = render_to_string('email_verification.html', {
        'user': user,
        'domain': domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    
    try:
        # Create a multipart message
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = user.email
        msg['Subject'] = subject
        
        # Attach both plain text and HTML versions
        text_part = MIMEText('Please activate your account by clicking the link in this email.', 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Connect directly to Gmail's SSL port using with statement for proper cleanup
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
            # Send email
            server.send_message(msg)
        
        print(f"Verification email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        print("user found")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        print("User activated")
        messages.success(request, "Your account has been verified. You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid.")
        print("User inactivate")
        return redirect('signup')
    
def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                try:
                    Thread(target=send_verification_email, args=(user, request)).start()
                    messages.success(request, "Please verify your mail to activate your account")
                except Exception as e:
                    user.delete()
                    messages.error(request, f"An error occurred. Please try again later. Error: {str(e)}")
    else:
        form = SignUpForm()
    return render(request,'users/sign_up.html',{'form':form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
    else:
        u_form = UserUpdateForm(instance=request.user)
    profile = request.user.profile
    return render(request,'users/profile.html',{'u_form':u_form,'profile':profile})
