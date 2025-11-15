from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock', 'created_at', 'last_updated_at', 'is_active']
        read_only_fields = ['created_at', 'last_updated_at']
        

