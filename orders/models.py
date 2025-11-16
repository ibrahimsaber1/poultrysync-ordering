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
    
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='pending')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    related_name='created_orders')
    
    created_at = models.DateTimeField(auto_now_add=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.product.name} - (x{self.quantity})"
    
    @property
    def company(self):
        return self.created_by.company if self.created_by else None
    
    def clean(self):
        if self.product and not self.product.is_active: # checking the if the product is active
            raise ValidationError("Cannot order inactive products.")
        
        if self.product and self.quantity > self.product.stock: # checking the if the quantity is available
            raise ValidationError(
                f"Insufficient stock. Available: {self.product.stock}"
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
