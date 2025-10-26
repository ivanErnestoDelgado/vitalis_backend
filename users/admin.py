from django.contrib import admin
from .models import User,DoctorProfile

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display=('first_name','last_name')
    search_fields=('first_name','last_name','email')
    list_filter=('created_at',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display=()