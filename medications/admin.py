from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display=('description',)

@admin.register(DrugVariant)
class DrugVariantAdmin(admin.ModelAdmin):
    list_display=('drug','variant_name','dosage')

@admin.register(UnsafeMedication)
class UnsafeMedicationsAdmin(admin.ModelAdmin):
    list_display=('drug','patient','reason')