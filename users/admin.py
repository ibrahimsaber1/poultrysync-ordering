from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'company', 'role', 'is_staff']
    list_filter = ['role', 'company', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'company__name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Company Info', {'fields': ('company', 'role')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Company Info', {'fields': ('company', 'role')}),
    )
