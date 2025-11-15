from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """
        Data isolation: Non-superusers only see their own company.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.company.id)
    
    def has_add_permission(self, request):
        """Only superusers can create companies"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete companies"""
        return request.user.is_superuser
    
    def has_module_permission(self, request):
        """Allow staff users to view this module"""
        return request.user.is_staff or request.user.is_superuser
