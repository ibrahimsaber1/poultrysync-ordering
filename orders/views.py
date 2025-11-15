import csv
import logging
from datetime import date
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from .models import Order
from .serializers import OrderSerializer
from products.models import Product

logger = logging.getLogger('orders')

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Check user role
        if request.user.role == 'viewer':
            return Response(
                {'error': 'Viewers cannot place orders'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Support multiple orders
        orders_data = request.data if isinstance(request.data, list) else [request.data]
        
        created_orders = []
        errors = []
        
        with transaction.atomic():
            for order_data in orders_data:
                serializer = self.get_serializer(data=order_data)
                
                try:
                    serializer.is_valid(raise_exception=True)
                    order = serializer.save(created_by=request.user)
                    
                    # Deduct stock
                    product = order.product
                    product.stock -= order.quantity
                    product.save()
                    
                    # Update status to success and set shipped_at
                    order.status = 'success'
                    order.shipped_at = timezone.now()
                    order.save()
                    
                    # Log confirmation email
                    logger.info(
                        f"ORDER CONFIRMATION EMAIL\n"
                        f"To: {request.user.email}\n"
                        f"Subject: Order #{order.id} Confirmed\n"
                        f"Order Details:\n"
                        f"  - Product: {product.name}\n"
                        f"  - Quantity: {order.quantity}\n"
                        f"  - Total: ${product.price * order.quantity}\n"
                        f"  - Status: {order.status}\n"
                        f"  - Shipped At: {order.shipped_at}\n"
                    )
                    
                    created_orders.append(serializer.data)
                except Exception as e:
                    errors.append(str(e))
        
        if errors:
            return Response(
                {'errors': errors, 'created': created_orders},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(created_orders, status=status.HTTP_201_CREATED)

class OrderExportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Check if user can edit today's orders (for operator)
        orders = Order.objects.filter(
            created_by__company=request.user.company
        )
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Product', 'Quantity', 'Status', 'Created By', 'Created At', 'Shipped At'])
        
        for order in orders:
            writer.writerow([
                order.id,
                order.product.name,
                order.quantity,
                order.status,
                order.created_by.username if order.created_by else 'N/A',
                order.created_at,
                order.shipped_at
            ])
        
        return response
