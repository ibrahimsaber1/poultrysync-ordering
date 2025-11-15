import csv
import logging
from datetime import date
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Order
from .serializers import OrderSerializer
from products.models import Product

logger = logging.getLogger('orders')


@login_required
def create_order(request):
    """
    Handle order creation from HTML form.
    Constraint: viewer users cannot place orders.
    """
    if request.method == 'POST':
        # Check user role
        if request.user.role == 'viewer':
            messages.error(request, 'Viewers cannot place orders.')
            return redirect('index')
        
        try:
            product_id = request.POST.get('product')
            quantity = int(request.POST.get('quantity'))
            
            if not product_id or quantity <= 0:
                messages.error(request, 'Invalid product or quantity.')
                return redirect('index')
            
            # Get product
            product = Product.objects.get(
                id=product_id,
                company=request.user.company,
                is_active=True
            )
            
            # Validate stock
            if quantity > product.stock:
                messages.error(
                    request,
                    f'Insufficient stock. Available: {product.stock}'
                )
                return redirect('index')
            
            # Create order
            with transaction.atomic():
                order = Order.objects.create(
                    product=product,
                    quantity=quantity,
                    created_by=request.user,
                    status='success',
                    shipped_at=timezone.now()
                )
                
                # Deduct stock
                product.stock -= quantity
                product.save()
                
                # Log confirmation email
                logger.info(
                    f"ORDER CONFIRMATION EMAIL\n"
                    f"To: {request.user.email or request.user.username}\n"
                    f"Order Num. : #{order.id}\n"
                    f"- Product: {product.name}\n"
                    f"- Quantity :  {quantity}\n"
                    f"- Total: ${product.price * quantity}\n"
                    f"- Status: Success\n"
                    f"- Shipped At: {order.shipped_at}\n"
                    f"******************************************"
                )
                
                messages.success(
                    request,
                    f'Order #{order.id} placed successfully! '
                    f'{product.name} (x{quantity})'
                )
        
        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')
        except ValueError:
            messages.error(request, 'Invalid quantity value.')
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
    
    return redirect('index')


@login_required
def export_orders(request):
    """Export user's company orders as CSV"""
    orders = Order.objects.filter(
        created_by__company=request.user.company
    ).select_related('product', 'created_by').order_by('-created_at')
    
    response = HttpResponse(content_type='text/csv')
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response['Content-Disposition'] = f'attachment; filename="orders_{timestamp}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Product', 'Quantity', 'Status', 'Created By', 'Created At', 'Shipped At'])
    
    for order in orders:
        writer.writerow([
            order.id,
            order.product.name,
            order.quantity,
            order.get_status_display(),
            order.created_by.username if order.created_by else 'N/A',
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            order.shipped_at.strftime('%Y-%m-%d %H:%M:%S') if order.shipped_at else 'N/A',
        ])
    
    return response


# ==================== API VIEWS (CBV) ====================

class OrderCreateAPIView(generics.CreateAPIView):
    """API endpoint for creating orders"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if request.user.role == 'viewer':
            return Response(
                {'error': 'Viewers cannot place orders'},
                status=status.HTTP_403_FORBIDDEN
            )

        is_bulk = isinstance(request.data, list)
        orders_data = request.data if is_bulk else [request.data]

        created_orders = []
        errors = []

        with transaction.atomic():
            for index, order_data in enumerate(orders_data):
                serializer = self.get_serializer(data=order_data)

                try:
                    serializer.is_valid(raise_exception=True)
                    order = serializer.save(created_by=request.user)

                    product = order.product
                    product.stock -= order.quantity
                    product.save(update_fields=['stock'])

                    order.status = 'success'
                    order.shipped_at = timezone.now()
                    order.save(update_fields=['status', 'shipped_at'])

                    logger.info(
                        f"ORDER CONFIRMATION EMAIL\n"
                        f"To: {request.user.email}\n"
                        f"Order #{order.id} - {product.name}\n"
                        f"Quantity: {order.quantity}\n"
                        f"Total: ${product.price * order.quantity}\n"
                    )

                    created_orders.append(serializer.data)

                except Exception as e:
                    errors.append(f"Order {index + 1}: {str(e)}")

        if errors and not created_orders:
            return Response(
                {'success': False, 'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                'success': True,
                'created': created_orders,
                'message': f'{len(created_orders)} order(s) created'
            },
            status=status.HTTP_201_CREATED
        )


class OrderExportAPIView(generics.GenericAPIView):
    """API endpoint to export orders as CSV"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(
            created_by__company=request.user.company
        ).select_related('product', 'created_by')

        response = HttpResponse(content_type='text/csv')
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response['Content-Disposition'] = f'attachment; filename="orders_{timestamp}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Product', 'Quantity', 'Status', 'Created By', 'Created At', 'Shipped At'])

        for order in orders:
            writer.writerow([
                order.id,
                order.product.name,
                order.quantity,
                order.get_status_display(),
                order.created_by.username if order.created_by else 'N/A',
                order.created_at,
                order.shipped_at
            ])

        return response
