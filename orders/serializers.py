from rest_framework import serializers
from .models import Order
from products.models import Product
from django.utils import timezone

class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'product', 'product_name', 'quantity', 'status', 'created_at', 'shipped_at']
        read_only_fields = ['created_at', 'shipped_at']
        
    def validate(self, data):
        product = data.get('product')
        quantity = data.get('quantity')

            # Check if product is active
        if not product.is_active:
            raise serializers.ValidationError("Cannot order inactive products.")
        
        # Check if user's company matches product's company
        user = self.context['request'].user
        if product.company != user.company:
            raise serializers.ValidationError("You can only order products from your company.")
        
        # check stock avilability
        if quantity > product.stock:
            raise serializers.ValidationError(
                f"the order quantity is not available on the stock. Available: {product.stock}")
        
        return data