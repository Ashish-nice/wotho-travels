from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name='home'),
    path("bus-booking/", views.BusListView.as_view(), name='bus_list'), 
    path("bus-detail/<pk>/", views.BusDetailView.as_view(), name='bus_detail'),
]