from django.shortcuts import render,redirect
from .forms import SignUpForm
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


        