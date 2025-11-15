from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('operator', 'Operator'),
        ('viewer', 'Viewer'),
    )
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='users'
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    
    class Meta:
        ordering = ['username']
    
    def __str__(self):
        return f"{self.username} from: {self.company}"
