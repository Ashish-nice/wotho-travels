from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.BusAdminLoginView.as_view(), name='bus_admin_login'),
    path("dashboard/", views.BusAdminDashboardView.as_view(), name='bus_admin_dashboard'),
]
