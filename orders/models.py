from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# Create your models here.

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    
    product = models.ForeignKey( 'products.Product',
                                on_delete=models.CASCADE,
                                related_name='orders')
    
    quantity = models.PositiveBigIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='pending')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete= models.SET_NULL,
                                   related_name='created_orders')
    
    created_at = models.DateTimeField(auto_now_add=True)
    shipped_at = models.DateTimeField(null=True, blank=True)