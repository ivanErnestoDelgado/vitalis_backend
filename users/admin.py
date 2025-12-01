from django.contrib import admin
from .models import User,DoctorProfile,CustomFCMDevice

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display=('first_name','last_name')
    search_fields=('first_name','last_name','email')
    list_filter=('created_at',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display=()

@admin.register(CustomFCMDevice)
class CustomFCMDeviceAdmin(admin.ModelAdmin):
    list_display=('registration_id','name','active','date_created')
    search_fields=('registration_id','name')
    list_filter=('active','date_created')   