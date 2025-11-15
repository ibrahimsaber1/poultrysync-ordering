from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['company', 'is_active', 'created_at']
    search_fields = ['name', 'company__name']
    readonly_fields = ['created_by', 'created_at', 'last_updated_at']
    
    actions = ['mark_inactive']
    
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
    mark_inactive.short_description = "Mark selected products as inactive"
    
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
