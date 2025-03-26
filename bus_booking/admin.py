from django.contrib import admin
#from django.contrib.auth.models import Group
#from django.contrib.sites.models import Site
#from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
#from allauth.account.models import EmailAddress
from .models import Bus, Booking, Schedule, City, Journey, Ticket
#Making my admin page look good

admin.site.site_header = 'Wotho travels Admin page'
admin.site.site_title = 'Wotho Admin'

class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra=0

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'capacity')
    search_fields = ('name', 'number')
    inlines = [ScheduleInline]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bus', 'from_city', 'to_city', 'booking_payment')
    search_fields = ('id', 'user__user__username')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'date', 'seats')
    search_fields = ('schedule__bus__name', 'date')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('booking', 'name', 'age')
    search_fields = ('booking__id', 'name')
#admin.site.unregister(Group)
#admin.site.unregister(Site)
#admin.site.unregister(SocialAccount)
#admin.site.unregister(SocialApp)
#admin.site.unregister(SocialToken)
#admin.site.unregister(EmailAddress)