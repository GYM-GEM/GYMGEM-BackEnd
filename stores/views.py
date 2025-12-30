from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    StoreSerializer, StoreBranchSerializer, StoreItemSerializer,
    OrderSerializer, OrderItemSerializer, AddOrderItemSerializer
)
from .models import Store, StoreBranch, StoreItem, Order, OrderItem, StoreItemSize
from authenticationAndAuthorization.permissions import HasRole
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from utils.views import get_profile_id_from_token
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import Account
from django.db.models import Q

class StoreListView(APIView):
    permission_classes = [HasRole(["store"])]

    @extend_schema(
        summary="List stores",
        description="Retrieve all stores",
        responses={200: StoreSerializer(many=True)}
    )
    def get(self, request):
        stores = Store.objects.all()
        serializer = StoreSerializer(stores, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Create a new store",
        description="Create a new store",
        request=StoreSerializer,
        responses={201: StoreSerializer}
    )
    def post(self, request):
        serializer = StoreSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get store details",
        description="Retrieve details of a specific store",
        responses={200: StoreSerializer}
    )
    def get(self, request, profile_id):
        store = get_object_or_404(Store, profile_id=profile_id)
        serializer = StoreSerializer(store, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update store",
        description="Update a store (only by owner)",
        request=StoreSerializer,
        responses={200: StoreSerializer}
    )
    def put(self, request, profile_id):
        store = get_object_or_404(Store, profile_id=profile_id)
        if not self._is_owner(request, store):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreSerializer(store, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially update store",
        description="Partially update a store (only by owner)",
        request=StoreSerializer,
        responses={200: StoreSerializer}
    )
    def patch(self, request, profile_id):
        store = get_object_or_404(Store, profile_id=profile_id)
        if not self._is_owner(request, store):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreSerializer(store, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete store",
        description="Delete a store (only by owner)",
        responses={204: None}
    )
    def delete(self, request, profile_id):
        store = get_object_or_404(Store, profile_id=profile_id)
        if not self._is_owner(request, store):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _is_owner(self, request, store):
        profile_id = get_profile_id_from_token(request)
        return store.profile_id.id == profile_id

class StoreBranchView(APIView):
    permission_classes = [HasRole(["store"])]

    @extend_schema(
        summary="List store branches",
        description="Retrieve all store branches",
        responses={200: StoreBranchSerializer(many=True)}
    )
    def get(self, request):
        storebranches = StoreBranch.objects.all()
        serializer = StoreBranchSerializer(storebranches, many=True, context={"request": request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Create store branch",
        description="Create a new store branch (only by store owner)",
        request=StoreBranchSerializer,
        responses={201: StoreBranchSerializer}
    )
    def post(self, request):
        serializer = StoreBranchSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class StoreBranchUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get store branch details",
        description="Retrieve details of a specific store branch",
        responses={200: StoreBranchSerializer}
    )
    def get(self, request, branch_id):
        storebranch = get_object_or_404(StoreBranch, id=branch_id)
        serializer = StoreBranchSerializer(storebranch, context={"request": request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Update store branch",
        description="Update a store branch (only by store owner)",
        request=StoreBranchSerializer,
        responses={200: StoreBranchSerializer}
    )
    def put(self, request, branch_id):
        storebranch = get_object_or_404(StoreBranch, id=branch_id)
        if not self._is_owner(request, storebranch.store_id):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = StoreBranchSerializer(storebranch, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete store branch",
        description="Delete a store branch (only by store owner)",
        responses={204: None}
    )
    def delete(self, request, branch_id):
        storebranch = get_object_or_404(StoreBranch, id=branch_id)
        if not self._is_owner(request, storebranch.store_id):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        storebranch.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Partially update store branch",
        description="Partially update a store branch (only by store owner)",
        request=StoreBranchSerializer,
        responses={200: StoreBranchSerializer}
    )
    def patch(self, request, branch_id):
        storebranch = get_object_or_404(StoreBranch, id=branch_id)
        if not self._is_owner(request, storebranch.store_id):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = StoreBranchSerializer(storebranch, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _is_owner(self, request, store):
        profile_id = get_profile_id_from_token(request)
        return store.profile_id.id == profile_id

class StoreItemListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List store items with filters",
        description="Retrieve all store items with optional filtering and search",
        parameters=[
            OpenApiParameter(name="store_id", type=OpenApiTypes.INT, description="Filter by store ID"),
            OpenApiParameter(name="branch_id", type=OpenApiTypes.INT, description="Filter by branch ID"),
            OpenApiParameter(name="category", type=OpenApiTypes.STR, description="Filter by category (supplements, clothes, foods)"),
            OpenApiParameter(name="price_min", type=OpenApiTypes.DECIMAL, description="Minimum price filter"),
            OpenApiParameter(name="price_max", type=OpenApiTypes.DECIMAL, description="Maximum price filter"),
            OpenApiParameter(name="search", type=OpenApiTypes.STR, description="Search in name, description, and brand"),
            OpenApiParameter(name="ordering", type=OpenApiTypes.STR, description="Order by field (name, price, -name, -price)"),
        ],
        responses={200: StoreItemSerializer(many=True)}
    )
    
    def get(self, request):
        params = request.query_params
        queryset = StoreItem.objects.select_related('store_id', 'branch_id')

        if params.get("store_id"):
            queryset = queryset.filter(store_id=params["store_id"])

        if params.get("branch_id"):
            queryset = queryset.filter(branch_id=params["branch_id"])

        if params.get("category"):
            queryset = queryset.filter(category=params["category"])

        price_min = params.get("price_min")
        price_max = params.get("price_max")
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        if params.get("search"):
            search_term = params["search"]
            queryset = queryset.filter(
                Q(name__icontains=search_term) | Q(description__icontains=search_term) | Q(brand__icontains=search_term)
            )

        if params.get("ordering"):
            queryset = queryset.order_by(params["ordering"])

        serializer = StoreItemSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Create store item",
        description="Create a new store item (only by store owner)",
        request=StoreItemSerializer,
        responses={201: StoreItemSerializer}
    )
    def post(self, request):
        serializer = StoreItemSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class MyStoreItemListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List my store items",
        description="Retrieve all items belonging to the authenticated store owner",
        responses={200: StoreItemSerializer(many=True)}
    )
    def get(self, request):
        profile_id = get_profile_id_from_token(request)
        if not profile_id:
             return Response({"detail": "Profile not found."}, status=status.HTTP_400_BAD_REQUEST)
             
        try:
            store = Store.objects.get(profile_id=profile_id)
        except Store.DoesNotExist:
             return Response({"detail": "Store not found for this user."}, status=status.HTTP_404_NOT_FOUND)
             
        items = StoreItem.objects.filter(store_id=store)
        serializer = StoreItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)


class StoreItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get store item details",
        description="Retrieve details of a specific store item",
        responses={200: StoreItemSerializer}
    )
    def get(self, request, item_id):
        item = get_object_or_404(StoreItem, id=item_id)
        serializer = StoreItemSerializer(item, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update store item",
        description="Update a store item (only by store owner)",
        request=StoreItemSerializer,
        responses={200: StoreItemSerializer}
    )
    def put(self, request, item_id):
        item = get_object_or_404(StoreItem, id=item_id)
        if not self._is_store_owner_of_item(request, item):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreItemSerializer(item, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially update store item",
        description="Partially update a store item (only by store owner)",
        request=StoreItemSerializer,
        responses={200: StoreItemSerializer}
    )
    def patch(self, request, item_id):
        item = get_object_or_404(StoreItem, id=item_id)
        if not self._is_store_owner_of_item(request, item):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreItemSerializer(item, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete store item",
        description="Delete a store item (only by store owner)",
        responses={204: None}
    )
    def delete(self, request, item_id):
        item = get_object_or_404(StoreItem, id=item_id)
        if not self._is_store_owner_of_item(request, item):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    def _is_store_owner_of_item(self, request, item):
        if not item:
            return False
        profile_id = get_profile_id_from_token(request)
        return item.store_id.profile_id.id == profile_id

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List orders",
        description="Retrieve orders filtered by store or buyer",
        parameters=[
            OpenApiParameter(name='store_id', type=OpenApiTypes.INT, description='Filter by store ID'),
            OpenApiParameter(name='buyer_id', type=OpenApiTypes.INT, description='Filter by buyer ID'),
        ],
        responses={200: OrderSerializer(many=True)}
    )
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
        profile_id = get_profile_id_from_token(request)
        if profile_id:
            user_stores = Store.objects.filter(profile_id=profile_id)
            if user_stores.exists():
                orders = orders.filter(store_id__in=user_stores)
        
        # Filter by store_id if provided
        store_id = request.query_params.get('store_id')
        if store_id:
            orders = orders.filter(store_id=store_id)
        
        # Filter by buyer_id if provided
        buyer_id = request.query_params.get('buyer_id')
        if buyer_id:
            orders = orders.filter(buyer_id=buyer_id)
        
        # If user is authenticated but not a store owner, show their own orders
        if request.user and request.user.is_authenticated and not profile_id:
            orders = orders.filter(buyer_id=request.user.id)
        
        serializer = OrderSerializer(orders, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create order",
        description="Create a new order",
        request=OrderSerializer,
        responses={201: OrderSerializer}
    )
    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get order details",
        description="Retrieve details of a specific order",
        responses={200: OrderSerializer}
    )
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update order",
        description="Update an order (store owner or buyer only)",
        request=OrderSerializer,
        responses={200: OrderSerializer}
    )
    def put(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not self._can_edit_order(request, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderSerializer(order, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            order.calculate_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially update order",
        description="Partially update an order (store owner or buyer only)",
        request=OrderSerializer,
        responses={200: OrderSerializer}
    )
    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not self._can_edit_order(request, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderSerializer(order, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            order.calculate_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete order",
        description="Delete an order (store owner only)",
        responses={204: None}
    )
    def delete(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not self._can_delete_order(request, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _can_edit_order(self, request, order):
        if not order:
            return False
        profile_id = get_profile_id_from_token(request)
        # Store owner or buyer can edit
        is_store_owner = order.store_id.profile_id.id == profile_id
        is_buyer = order.buyer_id.id == request.user.id
        return is_store_owner or is_buyer

    def _can_delete_order(self, request, order):
        if not order:
            return False
        profile_id = get_profile_id_from_token(request)
        # Only store owner or buyer
        is_store_owner = order.store_id.profile_id.id == profile_id
        is_buyer = order.buyer_id.id == request.user.id
        return is_store_owner or is_buyer

class OrderItemListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List order items for a specific order",
        description="Retrieve all order items for a specific order",
        responses={200: OrderItemSerializer(many=True)}
    )
    def get(self, request, order_id):
        # Get the specific order
        order = get_object_or_404(Order, id=order_id)
        
        # Check permissions: store owner or buyer
        profile_id = get_profile_id_from_token(request)
        is_store_owner = order.store_id.profile_id.id == profile_id
        is_buyer = order.buyer_id.id == request.user.id
        
        if not (is_store_owner or is_buyer):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        # Get items for this order
        items = OrderItem.objects.filter(order_id=order)
        serializer = OrderItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Add item to order",
        description="Add an item to an order (store owner or buyer only)",
        request=AddOrderItemSerializer,
        responses={201: OrderItemSerializer}
    )
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        
        # Check permission: store owner or buyer
        if not self._can_edit_order_items(request, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AddOrderItemSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            store_item_id = serializer.validated_data['store_item_id']
            size_id = serializer.validated_data.get('size_id')
            quantity = serializer.validated_data['quantity']
            
            item = get_object_or_404(StoreItem, id=store_item_id)
            
            # Get size instance if provided
            size_instance = None
            if size_id is not None:
                size_instance = get_object_or_404(StoreItemSize, id=size_id)
            
            # Create order item
            order_item = OrderItem.objects.create(
                order_id=order,
                store_item_id=item,
                size_id=size_instance,
                quantity=quantity,
                price_at_order=item.price
            )
            order.calculate_total()
            
            item_serializer = OrderItemSerializer(order_item, context={"request": request})
            return Response(item_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _can_edit_order_items(self, request, order):
        profile_id = get_profile_id_from_token(request)
        is_store_owner = order.store_id.profile_id.id == profile_id
        is_buyer = order.buyer_id.id == request.user.id
        return is_store_owner or is_buyer


class OrderItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get order item details",
        description="Retrieve details of a specific order item",
        responses={200: OrderItemSerializer}
    )
    def get(self, request, order_item_id):
        item = get_object_or_404(OrderItem, id=order_item_id)
        serializer = OrderItemSerializer(item, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Delete order item",
        description="Delete an order item (store owner or buyer only)",
        responses={204: None}
    )
    def delete(self, request, order_item_id):
        item = get_object_or_404(OrderItem, id=order_item_id)
        
        order = item.order_id
        if not self._can_delete_item(request, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        item.delete()
        order.calculate_total()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _can_delete_item(self, request, order):
        profile_id = get_profile_id_from_token(request)
        # Only store owner or buyer
        is_store_owner = order.store_id.profile_id.id == profile_id
        is_buyer = order.buyer_id.id == request.user.id
        return is_store_owner or is_buyer
    
    @extend_schema(
        summary="Update order item",
        description="Update an order item (store owner or buyer only)",
        request=OrderItemSerializer,
        responses={200: OrderItemSerializer}
    )
    
    def patch (self, request, order_item_id):
        item = get_object_or_404(OrderItem, id=order_item_id)
        order = item.order_id
        
        if not self._can_delete_item(request, order):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderItemSerializer(item, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            order.calculate_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)