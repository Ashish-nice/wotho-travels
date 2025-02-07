from django.shortcuts import render,redirect
from .forms import SignUpForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

# Create your views here.

def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request,'users/sign_up.html',{'form':form})

@login_required
def profile(request):
    profile = request.user.profile
    return render(request,'users/profile.html',{'profile':profile})