from django.contrib import admin
#from django.contrib.auth.models import Group
#from django.contrib.sites.models import Site
#from allauth.socialaccount import SocialAccount, SocialApp, SocialToken
from allauth.account.models import EmailAddress
from .models import Bus, Booking, BusFare, Schedule, City
#Making my admin page look good
class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1
    
class BusFareInline(admin.TabularInline):
    model = BusFare
    extra = 1

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'capacity')
    search_fields = ('name', 'number')
    inlines = [ScheduleInline, BusFareInline]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bus', 'from_city', 'to_city', 'status')
    list_filter = ('status', 'time')
    search_fields = ('id', 'user__user__username')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
admin.site.register(BusFare)
#admin.site.unregister(Group)
#admin.site.unregister(Site)
#admin.site.unregister(SocialAccount)
#admin.site.unregister(SocialApp)
#admin.site.unregister(SocialToken)
#admin.site.unregister(EmailAddress)