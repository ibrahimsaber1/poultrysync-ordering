from django.db import models
from django.conf  import settings
# Create your models here.

class Product(models.Model):
    company = models.ForeignKey( 'companies.Company',
                                on_delete= models.CASCADE, related_name='products')
    
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey( settings.AUTH_USER_MODEL,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    related_name='created_products') 
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['company', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.company.name})"