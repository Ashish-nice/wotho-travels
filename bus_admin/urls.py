from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.BusAdminLoginView.as_view(), name='bus_admin_login'),
    path("logout/", views.BusAdminLogoutView.as_view(), name='bus_admin_logout'),
    path("dashboard/", views.BusAdminDashboardView.as_view(), name='bus_admin_dashboard'),
    path("buses/", views.BusListView.as_view(), name='admin_bus_list'),
    path("bookings/", views.BookingListView.as_view(), name='admin_booking_list'),
    path('buses/<int:bus_id>/schedule/', views.GetBusScheduleView.as_view(), name='get_bus_schedule'),
    path('buses/<int:bus_id>/detail/', views.GetBusDetailView.as_view(), name='get_bus_detail'),
    path('buses/add/', views.AddBusView.as_view(), name='add_bus'),
    path('buses/<int:bus_id>/update/', views.UpdateBusView.as_view(), name='update_bus'),
    path('buses/<int:bus_id>/delete/', views.CancelBusView.as_view(), name='delete_bus'),
    path('export-bookings/', views.export_bookings, name='export_bookings'),
]
