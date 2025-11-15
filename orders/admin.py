import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'quantity', 'status', 'created_by', 'created_at', 'shipped_at']
    list_filter = ['status', 'created_at', 'product__company']
    search_fields = ['product__name', 'created_by__username']
    readonly_fields = ['created_by', 'created_at', 'shipped_at']
    
    actions = ['export_as_csv']
    
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = ['id', 'product', 'quantity', 'status', 'created_by', 'created_at', 'shipped_at']
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)
        
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        
        return response
    
    export_as_csv.short_description = "Export selected orders as CSV"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
