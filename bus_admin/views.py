from django.contrib.auth.models import Group
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.contrib import messages
# Create your views here.
class BusAdminLoginView(FormView):
    template_name = 'bus_admin/login.html'
    form_class = AuthenticationForm
    success_url = '/bus-admin/dashboard/'  

    def form_valid(self, form):
        user = form.get_user()
        if user.groups.filter(name='BusAdmin').exists():
            return super().form_valid(form)
        else:
            messages.error(self.request, 'You are not authorized to access this section.')
            return render(self.request,'bus_admin/login.html', {'form': form})

