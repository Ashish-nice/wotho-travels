from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings

urlpatterns = [
    path('sign-up/', views.sign_up, name='users/sign_up'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    #path('logout/', views.logout_view, name='users/logout'),
    #path('profile/', views.profile, name='users/profile'),
]
