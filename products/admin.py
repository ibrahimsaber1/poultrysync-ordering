from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'price', 'stock', 'is_active', 'created_by', 'created_at']
    list_filter = ['company', 'is_active', 'created_at']
    search_fields = ['name', 'company__name']
    readonly_fields = ['created_by', 'created_at', 'last_updated_at']
    
    actions = ['mark_inactive']
    
    def mark_inactive(self, request, queryset):
        """Bulk action: mark selected products inactive (soft-delete)"""
        # Only allow users to soft-delete their own company's products
        if not request.user.is_superuser:
            queryset = queryset.filter(company=request.user.company)
        
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} product(s) marked as inactive.')
    
    mark_inactive.short_description = "Mark selected products inactive"
    
    def save_model(self, request, obj, form, change):
        """Auto-fill created_by and company when creating new product"""
        if not change:
            obj.created_by = request.user
            # Auto-fill company from user if not set
            if not obj.company:
                obj.company = request.user.company
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Data isolation: Users only see products from their company.
        Superuser sees all products.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)
    
    def has_change_permission(self, request, obj=None):
        """
        Users can edit products from their company.
        """
        if request.user.is_superuser:
            return True
        
        # Viewers cannot edit
        if request.user.role == 'viewer':
            return False
        
        # If checking specific object, ensure it's from user's company
        if obj and obj.company != request.user.company:
            return False
        
        return True
    
    def has_delete_permission(self, request, obj=None):
        """
        Only admins can delete products.
        """
        if request.user.is_superuser:
            return True
        
        if request.user.role == 'admin':
            if obj and obj.company == request.user.company:
                return True
        
        return False
    
    def has_add_permission(self, request):
        """Admin and operator can add products"""
        if request.user.is_superuser:
            return True
        
        return request.user.role in ['admin', 'operator']
    
    def has_module_permission(self, request):
        """Allow staff users to access this module"""
        return request.user.is_staff or request.user.is_superuser
