import csv
from datetime import date
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from .models import Order
from products.models import Product


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'quantity', 'status', 'created_by', 'created_at', 'shipped_at']
    list_filter = ['status', 'created_at', 'product__company']
    search_fields = ['product__name', 'created_by__username']
    readonly_fields = ['created_by', 'created_at', 'shipped_at']
    
    actions = ['export_as_csv']
    
    def export_as_csv(self, request, queryset):
        """Admin Action: Export selected orders as CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="orders_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Order ID', 'Product', 'Quantity', 'Status', 
            'Created By', 'Created At', 'Shipped At', 'Company'
        ])
        
        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.product.name,
                obj.quantity,
                obj.get_status_display(),
                obj.created_by.username if obj.created_by else 'N/A',
                obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                obj.shipped_at.strftime('%Y-%m-%d %H:%M:%S') if obj.shipped_at else 'N/A',
                obj.created_by.company.name if obj.created_by else 'N/A'
            ])
        
        self.message_user(request, f'{queryset.count()} order(s) exported.')
        return response
    
    export_as_csv.short_description = "Export selected orders as CSV"
    
    def save_model(self, request, obj, form, change):
        """Auto-fill created_by when creating new order"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Data Isolation: Users only see orders from their company.
        Superuser sees all orders.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by__company=request.user.company)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filter product dropdown to show only user's company products.
        This fixes the issue where admin can't see their company's products.
        """
        if db_field.name == "product":
            if not request.user.is_superuser:
                # Filter products to only show active products from user's company
                kwargs["queryset"] = Product.objects.filter(
                    company=request.user.company,
                    is_active=True
                )
            else:
                # Superuser sees all active products
                kwargs["queryset"] = Product.objects.filter(is_active=True)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def has_change_permission(self, request, obj=None):
        """
        CONSTRAINT: operator users may edit only orders created today.
        
        Permission Logic:
        - Superuser: Can edit ANY order
        - Admin role: Can edit ANY order from their company
        - Operator role: Can ONLY edit orders created TODAY (from their company)
        - Viewer role: CANNOT edit any orders
        """
        # Superusers can do anything
        if request.user.is_superuser:
            return True
        
        # Viewers cannot edit
        if request.user.role == 'viewer':
            return False
        
        # If checking list view (obj is None), allow access
        if obj is None:
            return True
        
        # Check if order belongs to user's company (data isolation)
        if obj.created_by and obj.created_by.company != request.user.company:
            return False
        
        # Admin role can edit all orders from their company
        if request.user.role == 'admin':
            return True
        
        # Operator role can only edit today's orders
        if request.user.role == 'operator':
            today = date.today()
            order_date = obj.created_at.date()
            
            if order_date == today:
                return True
            else:
                # Order is from a previous day - operator cannot edit
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
            # Check company isolation
            if obj.created_by.company != request.user.company:
                return False
        
        if request.user.role == 'admin':
            return True
        
        # Operators and viewers cannot delete orders
        return False
    
    def has_add_permission(self, request):
        """
        Add permissions:
        - Viewers cannot add orders
        - Admin and Operator can add orders
        """
        if request.user.is_superuser:
            return True
        
        # Viewers cannot create orders
        if request.user.role == 'viewer':
            return False
        
        return True
    
    def has_module_permission(self, request):
        """Allow staff users (admin/operator) to access this module"""
        return request.user.is_staff or request.user.is_superuser
