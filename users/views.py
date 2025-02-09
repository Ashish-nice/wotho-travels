from django.shortcuts import render,redirect
from .forms import SignUpForm, UserUpdateForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
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