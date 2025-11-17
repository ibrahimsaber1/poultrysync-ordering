import csv
import logging
from datetime import date
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Order
from .serializers import OrderSerializer
from products.models import Product

logger = logging.getLogger('orders')


# ===== Shared Business Logic =====
class OrderService:
    """Service class to handle order business logic"""
    
    @staticmethod
    def process_order(product, quantity, user):
        """Process order: validate, create, deduct stock, log email"""
        # Validate stock
        if quantity > product.stock:
            raise ValueError(f'Insufficient stock. Available: {product.stock}')
        
        # Create order with transaction
        with transaction.atomic():
            order = Order.objects.create(
                product=product,
                quantity=quantity,
                created_by=user,
                status='success',
                shipped_at=timezone.now()
            )
            
            # Deduct stock
            product.stock -= quantity
            product.save(update_fields=['stock'])
            
            # Log confirmation email
            OrderService.log_confirmation_email(order, user)
        
        return order
    
    @staticmethod
    def log_confirmation_email(order, user):
        """Log order confirmation email"""
        product = order.product
        logger.info(
            f"ORDER CONFIRMATION EMAIL\n"
            f"hi there we want to let u know that your order is Successfully placed\n"
            f"See more info: - \n"
            f"To: {user.email or user.username}\n"
            f"Order Num. : #{order.id}\n"
            f"- Product: {product.name}\n"
            f"- Quantity : {order.quantity}\n"
            f"- Total: ${product.price * order.quantity}\n"
            f"- Status: Success\n"
            f"- Shipped At: {order.shipped_at}\n"
            f"*****************************************************"
        )
    
    @staticmethod
    def generate_csv_response(orders, filename_prefix='orders'):
        """Generate CSV response for orders"""
        response = HttpResponse(content_type='text/csv')
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timestamp}.csv"'
        
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



@method_decorator(login_required, name='dispatch')
class OrderCreateView(View):
    """Handle order creation from HTML form"""
    
    def post(self, request):
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
            
            product = Product.objects.get( id=product_id, company=request.user.company, is_active=True)
            order = OrderService.process_order(product, quantity, request.user)
            
            messages.success(request, f'Order #{order.id} placed successfully! {product.name} (x{quantity})')
            
        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
        
        return redirect('index')


@method_decorator(login_required, name='dispatch')
class OrderExportView(View):
    """Export user's company orders as CSV"""
    
    def get(self, request):
        orders = Order.objects.filter(
            created_by__company=request.user.company
        ).select_related('product', 'created_by').order_by('-created_at')
        
        return OrderService.generate_csv_response(orders)


class OrderCreateAPIView(generics.CreateAPIView):
    """API: Create one or more orders"""
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
                    
                    # Use service to process order
                    product = order.product
                    product.stock -= order.quantity
                    product.save(update_fields=['stock'])
                    
                    order.status = 'success'
                    order.shipped_at = timezone.now()
                    order.save(update_fields=['status', 'shipped_at'])
                    
                    OrderService.log_confirmation_email(order, request.user)
                    created_orders.append(serializer.data)
                except Exception as e:
                    errors.append(f"Order {index + 1}: {str(e)}")
        
        if errors and not created_orders:
            return Response(
                {'success': False, 'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'success': True,
            'created': created_orders,
            'message': f'{len(created_orders)} order(s) created'
        }, status=status.HTTP_201_CREATED)


class OrderExportAPIView(generics.GenericAPIView):
    """API: Export orders as CSV"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(
            created_by__company=request.user.company
        ).select_related('product', 'created_by')
        
        return OrderService.generate_csv_response(orders)


# Convert class-based views to function-based for URL routing
create_order = OrderCreateView.as_view()
export_orders = OrderExportView.as_view()
