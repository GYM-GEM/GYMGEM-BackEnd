from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    StoreSerializer, StoreBranchSerializer, StoreItemSerializer,
    OrderSerializer, OrderItemSerializer, AddOrderItemSerializer
)
from .models import Store, StoreBranch, StoreItem, Order, OrderItem

class StoreListView(APIView):
    """GET: Anyone can view stores | POST: Only store profile owners can create"""
    
    def get(self, request):
        stores = Store.objects.all()
        serializer = StoreSerializer(stores, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        # Only store profile owners can create
        if not self._is_store_owner(request.user):
            return Response({"detail": "Only store owners can create stores."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _is_store_owner(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.groups.filter(name__iexact='store').exists()


class StoreDetailView(APIView):
    """GET: Anyone can view | PUT/PATCH/DELETE: Only owner"""
    
    def get(self, request, store_id):
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response({"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StoreSerializer(store)
        return Response(serializer.data)

    def put(self, request, store_id):
        store = self._get_store_or_404(store_id)
        if store is None:
            return Response({"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._is_owner(request.user, store):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreSerializer(store, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, store_id):
        store = self._get_store_or_404(store_id)
        if store is None:
            return Response({"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._is_owner(request.user, store):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreSerializer(store, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, store_id):
        store = self._get_store_or_404(store_id)
        if store is None:
            return Response({"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._is_owner(request.user, store):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_store_or_404(self, store_id):
        try:
            return Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return None

    def _is_owner(self, user, store):
        if not user or not user.is_authenticated:
            return False
        return store.profile_id.account.id == user.id

class StoreBranchView(APIView):
    def get(self, request):
        storebranches = StoreBranch.objects.all()
        serializer = StoreBranchSerializer(storebranches, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = StoreBranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class StoreBranchUpdateView(APIView):
    def put(self, request, branch_id):
        try:
            storebranch = StoreBranch.objects.get(id=branch_id)
        except StoreBranch.DoesNotExist:
            return Response({"error": "StoreBranch not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = StoreBranchSerializer(storebranch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, branch_id):
        try:
            storebranch = StoreBranch.objects.get(id=branch_id)
        except StoreBranch.DoesNotExist:
            return Response({"error": "StoreBranch not found"}, status=status.HTTP_404_NOT_FOUND)

        storebranch.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, branch_id):
        try:
            storebranch = StoreBranch.objects.get(id=branch_id)
        except StoreBranch.DoesNotExist:
            return Response({"error": "StoreBranch not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = StoreBranchSerializer(storebranch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StoreItemListView(APIView):
    """GET: Anyone can view items | POST: Only store owner"""
    
    def get(self, request):
        items = StoreItem.objects.all()
        serializer = StoreItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Only store profile owners can add items
        if not self._is_store_owner(request.user):
            return Response({"detail": "Only store owners can add items."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _is_store_owner(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.groups.filter(name__iexact='store').exists()


class StoreItemDetailView(APIView):
    """GET: Anyone | PUT/PATCH/DELETE: Only store owner"""
    
    def get(self, request, item_id):
        try:
            item = StoreItem.objects.get(id=item_id)
        except StoreItem.DoesNotExist:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StoreItemSerializer(item)
        return Response(serializer.data)

    def put(self, request, item_id):
        item = self._get_item_or_404(item_id)
        if item is None:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._is_store_owner_of_item(request.user, item):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, item_id):
        item = self._get_item_or_404(item_id)
        if item is None:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._is_store_owner_of_item(request.user, item):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, item_id):
        item = self._get_item_or_404(item_id)
        if item is None:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._is_store_owner_of_item(request.user, item):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_item_or_404(self, item_id):
        try:
            return StoreItem.objects.get(id=item_id)
        except StoreItem.DoesNotExist:
            return None

    def _is_store_owner_of_item(self, user, item):
        if not user or not user.is_authenticated or not item:
            return False
        return item.store_id.profile_id.account.id == user.id

class OrderListView(APIView):
    """GET: Filter by store/buyer | POST: Authenticated users can create"""
    
    def get(self, request):
        """
        Query parameters:
        - store_id: Filter orders for a specific store
        - buyer_id: Filter orders by buyer account
        If authenticated user is store owner, show only their store's orders
        If authenticated user is buyer, show only their orders
        """
        orders = Order.objects.all()
        
        # If user is a store owner, filter to their store's orders
        if request.user and request.user.is_authenticated and self._is_store_owner(request.user):
            user_store = Store.objects.filter(profile_id__account=request.user).first()
            if user_store:
                orders = orders.filter(store_id=user_store)
        
        # Filter by store_id if provided
        store_id = request.query_params.get('store_id')
        if store_id:
            orders = orders.filter(store_id=store_id)
        
        # Filter by buyer_id if provided
        buyer_id = request.query_params.get('buyer_id')
        if buyer_id:
            orders = orders.filter(buyer_id=buyer_id)
        
        # If user is authenticated but not a store owner, show their own orders
        if request.user and request.user.is_authenticated and not self._is_store_owner(request.user):
            orders = orders.filter(buyer_id=request.user.id)
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Any authenticated user can create an order
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            # Set buyer as current user if not provided
            if 'buyer_id' not in request.data:
                serializer.validated_data['buyer_id'] = request.user
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _is_store_owner(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.groups.filter(name__iexact='store').exists()


class OrderDetailView(APIView):
    """GET: Anyone | PUT/PATCH: Store owner or buyer | DELETE: Store owner"""
    
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, order_id):
        order = self._get_order_or_404(order_id)
        if order is None:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_edit_order(request.user, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            order.calculate_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, order_id):
        order = self._get_order_or_404(order_id)
        if order is None:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_edit_order(request.user, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            order.calculate_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, order_id):
        order = self._get_order_or_404(order_id)
        if order is None:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_delete_order(request.user, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_order_or_404(self, order_id):
        try:
            return Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return None

    def _can_edit_order(self, user, order):
        if not user or not user.is_authenticated or not order:
            return False
        # Store owner or buyer can edit
        is_store_owner = order.store_id.profile_id.account.id == user.id
        is_buyer = order.buyer_id.id == user.id
        return is_store_owner or is_buyer

    def _can_delete_order(self, user, order):
        if not user or not user.is_authenticated or not order:
            return False
        # Only store owner or buyer
        is_store_owner = order.store_id.profile_id.account.id == user.id
        is_buyer = order.buyer_id.id == user.id
        return is_store_owner or is_buyer

class OrderItemListView(APIView):
    """GET: Anyone | POST: Add item to order - store owner or buyer"""
    
    def get(self, request):
        items = OrderItem.objects.all()
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permission: store owner or buyer
        if not self._can_edit_order_items(request.user, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AddOrderItemSerializer(data=request.data)
        if serializer.is_valid():
            store_item_id = serializer.validated_data['store_item_id']
            size_id = serializer.validated_data.get('size_id')
            quantity = serializer.validated_data['quantity']
            
            try:
                item = StoreItem.objects.get(id=store_item_id)
            except StoreItem.DoesNotExist:
                return Response({"detail": "Store item not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Create order item
            order_item = OrderItem.objects.create(
                order_id=order,
                store_item_id=item,
                size_id_id=size_id,
                quantity=quantity,
                price_at_order=item.price
            )
            order.calculate_total()
            
            item_serializer = OrderItemSerializer(order_item)
            return Response(item_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _can_edit_order_items(self, user, order):
        if not user or not user.is_authenticated:
            return False
        is_store_owner = order.store_id.profile_id.account.id == user.id
        is_buyer = order.buyer_id.id == user.id
        return is_store_owner or is_buyer


class OrderItemDetailView(APIView):
    """GET: Anyone | DELETE: Store owner or buyer"""
    
    def get(self, request, order_item_id):
        try:
            item = OrderItem.objects.get(id=order_item_id)
        except OrderItem.DoesNotExist:
            return Response({"detail": "Order item not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderItemSerializer(item)
        return Response(serializer.data)

    def delete(self, request, order_item_id):
        try:
            item = OrderItem.objects.get(id=order_item_id)
        except OrderItem.DoesNotExist:
            return Response({"detail": "Order item not found"}, status=status.HTTP_404_NOT_FOUND)
        
        order = item.order_id
        if not self._can_delete_item(request.user, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        item.delete()
        order.calculate_total()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _can_delete_item(self, user, order):
        if not user or not user.is_authenticated:
            return False
        is_store_owner = order.store_id.profile_id.account.id == user.id
        is_buyer = order.buyer_id.id == user.id
        return is_store_owner or is_buyer