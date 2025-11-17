import csv
from datetime import date
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from .models import Order
from products.models import Product
from .views import OrderService


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'quantity', 'status', 'created_by', 'created_at', 'shipped_at']
    list_filter = ['status', 'created_at', 'product__company']
    search_fields = ['product__name', 'created_by__username']
    readonly_fields = ['created_by', 'created_at', 'shipped_at']
    
    actions = ['export_as_csv']
    
    def export_as_csv(self, request, queryset):

        response = OrderService.generate_csv_response( orders=queryset, filename_prefix='admin_orders')
        self.message_user(request, f'{queryset.count()} order(s) exported.')
        return response
    
    export_as_csv.short_description = "Export selected orders as CSV"
    
    
    def save_model(self, request, obj, form, change):
        """Auto-fill created_by when creating new order"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Data Isolation: Users only see orders from their company.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by__company=request.user.company)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filter product dropdown to show only user's company products.
        """
        if db_field.name == "product":
            if not request.user.is_superuser:
                kwargs["queryset"] = Product.objects.filter(
                    company=request.user.company,
                    is_active=True
                )
            else:
                kwargs["queryset"] = Product.objects.filter(is_active=True)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    
    def has_change_permission(self, request, obj=None):
        """
        Permission Logic:
        - Superuser: Can edit ANY order
        - Admin role: Can edit ANY order from their company
        - Operator role: Can ONLY edit orders created TODAY (from their company)
        - Viewer role: CANNOT edit any orders
        """
        
        if request.user.is_superuser:
            return True
        
        if request.user.role == 'viewer':
            return False
        
        if obj is None:
            return True
        
        if obj.created_by and obj.created_by.company != request.user.company:
            return False
        
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'operator':
            today = date.today()
            order_date = obj.created_at.date()
            
            if order_date == today:
                return True
            else:
                return False
        
        # Default: deny
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Delete permissions:
        - Superuser: Can delete any order
        - Admin: Can delete orders from their company
        - Operator: CANNOT delete orders
        - Viewer: CANNOT delete orders
        """
        if request.user.is_superuser:
            return True
        
        if obj and obj.created_by:
            if obj.created_by.company != request.user.company:
                return False
        
        if request.user.role == 'admin':
            return True
        
        return False
    
    def has_add_permission(self, request):
        """
        Add permissions:
        - Viewers cannot add orders
        - Admin and Operator can add orders
        """
        if request.user.is_superuser:
            return True
        
        if request.user.role == 'viewer':
            return False
        
        return True
    
    def has_module_permission(self, request):
        """Allow staff users (admin/operator) to access this module"""
        return request.user.is_staff or request.user.is_superuser
