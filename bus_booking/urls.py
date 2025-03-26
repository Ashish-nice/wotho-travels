from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name='home'),
    path("bus-booking/", views.BusListView.as_view(), name='bus_list'), 
    path("bus-detail/<pk>/", views.BusDetailView.as_view(), name='bus_detail'),
    path("transact/", views.transact, name='transact'),
    path("checkout/", views.checkout, name='checkout'),
    path("verify-otp/", views.verify_otp, name='verify_otp'),
    path("resend-otp/", views.resend_otp, name='resend_otp'),
    path("bookings/", views.UserBookingsView.as_view(), name='bookings'),
    path("cancel-booking/<int:booking_id>/", views.cancel_booking, name='cancel_booking'),
    path("transaction-success/", views.transaction_success, name='transaction_success'),
]