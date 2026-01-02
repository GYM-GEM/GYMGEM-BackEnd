from urllib import request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    StoreSerializer,
    StoreBranchSerializer,
    StoreItemSerializer,
    OrderSerializer,
    OrderItemSerializer,
    AddOrderItemSerializer,
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
        summary="List all stores",
        description="Retrieve a list of all stores. Only accessible by users with 'store' role.",
        responses={
            200: StoreSerializer(many=True),
            403: "Forbidden - User does not have 'store' role",
        },
        tags=["Stores"],
    )
    def get(self, request):
        stores = Store.objects.all()
        serializer = StoreSerializer(stores, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create a new store",
        description="Create a new store for the authenticated user. The user must have a profile with type 'store'.",
        request=StoreSerializer,
        responses={
            201: StoreSerializer,
            400: "Bad Request - Invalid data or store already exists",
            403: "Forbidden - User does not have 'store' role",
        },
        tags=["Stores"],
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
        description="Retrieve details of a specific store by profile ID.",
        responses={200: StoreSerializer, 404: "Not Found - Store does not exist"},
        tags=["Stores"],
    )
    def get(self, request, profile_id):
        store = get_object_or_404(Store, profile_id=profile_id)
        serializer = StoreSerializer(store, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update store",
        description="Fully update a store. Only the store owner can perform this action.",
        request=StoreSerializer,
        responses={
            200: StoreSerializer,
            403: "Forbidden - User is not the store owner",
            404: "Not Found - Store does not exist",
        },
        tags=["Stores"],
    )
    def put(self, request, profile_id):
        store = get_object_or_404(Store, profile_id=profile_id)
        if not self._is_owner(request, store):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = StoreSerializer(
            store, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially update store",
        description="Partially update a store. Only the store owner can perform this action.",
        request=StoreSerializer,
        responses={
            200: StoreSerializer,
            403: "Forbidden - User is not the store owner",
            404: "Not Found - Store does not exist",
        },
        tags=["Stores"],
    )
    def patch(self, request, profile_id):
        store = get_object_or_404(Store, profile_id=profile_id)
        if not self._is_owner(request, store):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = StoreSerializer(
            store, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete store",
        description="Delete a store. Only the store owner can perform this action.",
        responses={
            204: "No Content - Store deleted successfully",
            403: "Forbidden - User is not the store owner",
            404: "Not Found - Store does not exist",
        },
        tags=["Stores"],
    )
    def delete(self, request, profile_id):
        store = get_object_or_404(Store, profile_id=profile_id)
        if not self._is_owner(request, store):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _is_owner(self, request, store):
        profile_id = get_profile_id_from_token(request)
        return store.profile_id.id == profile_id


class StoreBranchView(APIView):
    permission_classes = [HasRole(["store"])]

    @extend_schema(
        summary="List my store branches",
        description="Retrieve branches for the authenticated store owner.",
        responses={
            200: StoreBranchSerializer(many=True),
            400: "Bad Request - Profile not found",
            403: "Forbidden - User does not have 'store' role",
            404: "Not Found - Store not found",
        },
        tags=["Store Branches"],
    )
    def get(self, request):
        profile_id = get_profile_id_from_token(request)
        if not profile_id:
            return Response(
                {"detail": "Profile not found."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            store = Store.objects.get(profile_id=profile_id)
        except Store.DoesNotExist:
            return Response(
                {"detail": "Store not found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        queryset = StoreBranch.objects.filter(store_id=store)
        serializer = StoreBranchSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Create store branch",
        description="Create a new branch for the authenticated store owner's store.",
        request=StoreBranchSerializer,
        responses={
            201: StoreBranchSerializer,
            400: "Bad Request - Invalid data",
            403: "Forbidden - User does not have 'store' role",
        },
        tags=["Store Branches"],
    )
    def post(self, request):
        serializer = StoreBranchSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicStoreBranchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List store branches by profile ID",
        description="Retrieve branches for a store by profile ID. Accessible by authenticated users.",
        parameters=[
            OpenApiParameter(
                name="profile_id",
                type=OpenApiTypes.INT,
                description="Profile ID of the store owner",
                required=True,
            ),
        ],
        responses={
            200: StoreBranchSerializer(many=True),
            400: "Bad Request - profile_id required or invalid",
            404: "Not Found - Store not found",
        },
        tags=["Store Branches"],
    )
    def get(self, request):
        params = request.query_params
        profile_id = self.kwargs.get("profile_id") or params.get("profile_id")

        if not profile_id:
            return Response(
                {"detail": "profile_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            store = Store.objects.get(profile_id=profile_id)
        except Store.DoesNotExist:
            return Response(
                {"detail": "Store not found for this profile."},
                status=status.HTTP_404_NOT_FOUND,
            )
        store_id = store.id
        queryset = StoreBranch.objects.filter(store_id=store_id)
        serializer = StoreBranchSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)


class StoreBranchUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get store branch details",
        description="Retrieve details of a specific store branch including location and operating hours.",
        responses={
            200: StoreBranchSerializer,
            401: "Unauthorized - Authentication required",
            404: "Not Found - Branch not found",
        },
        tags=["Store Branches"],
    )
    def get(self, request, branch_id):
        storebranch = get_object_or_404(StoreBranch, id=branch_id)
        serializer = StoreBranchSerializer(storebranch, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update store branch",
        description="Fully update a store branch. Only the store owner can perform this action.",
        request=StoreBranchSerializer,
        responses={
            200: StoreBranchSerializer,
            400: "Bad Request - Invalid data",
            403: "Forbidden - Only store owner can update",
            404: "Not Found - Branch not found",
        },
        tags=["Store Branches"],
    )
    def put(self, request, branch_id):
        storebranch = get_object_or_404(StoreBranch, id=branch_id)
        if not self._is_owner(request, storebranch.store_id):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = StoreBranchSerializer(
            storebranch, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete store branch",
        description="Delete a store branch. Only the store owner can perform this action.",
        responses={
            204: "No Content - Branch deleted successfully",
            403: "Forbidden - Only store owner can delete",
            404: "Not Found - Branch not found",
        },
        tags=["Store Branches"],
    )
    def delete(self, request, branch_id):
        storebranch = get_object_or_404(StoreBranch, id=branch_id)
        if not self._is_owner(request, storebranch.store_id):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        storebranch.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Partially update store branch",
        description="Partially update a store branch (only by store owner)",
        request=StoreBranchSerializer,
        responses={200: StoreBranchSerializer},
    )
    def patch(self, request, branch_id):
        storebranch = get_object_or_404(StoreBranch, id=branch_id)
        if not self._is_owner(request, storebranch.store_id):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = StoreBranchSerializer(
            storebranch, data=request.data, partial=True, context={"request": request}
        )
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
        description="Retrieve all store items with optional filtering and search capabilities. Supports filtering by store, branch, category, price range, and text search.",
        parameters=[
            OpenApiParameter(
                name="store_id", type=OpenApiTypes.INT, description="Filter by store ID"
            ),
            OpenApiParameter(
                name="branch_id",
                type=OpenApiTypes.INT,
                description="Filter by branch ID",
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                description="Filter by category (supplements, clothes, foods)",
            ),
            OpenApiParameter(
                name="price_min",
                type=OpenApiTypes.INT,
                description="Minimum price filter (in cents)",
            ),
            OpenApiParameter(
                name="price_max",
                type=OpenApiTypes.INT,
                description="Maximum price filter (in cents)",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                description="Search in name, description, and brand",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                description="Order by field (name, price, -name, -price)",
            ),
        ],
        responses={
            200: StoreItemSerializer(many=True),
            401: "Unauthorized - Authentication required",
        },
        tags=["Store Items"],
    )
    def get(self, request):
        params = request.query_params
        queryset = StoreItem.objects.select_related("store_id", "branch_id")

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
                Q(name__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(brand__icontains=search_term)
            )

        if params.get("ordering"):
            queryset = queryset.order_by(params["ordering"])

        serializer = StoreItemSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Create store item",
        description="Create a new store item (only by store owner)",
        request=StoreItemSerializer,
        responses={201: StoreItemSerializer},
    )
    def post(self, request):
        serializer = StoreItemSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyStoreItemListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List my store items",
        description="Retrieve all items belonging to the authenticated store owner. Only shows items from stores owned by the user.",
        responses={
            200: StoreItemSerializer(many=True),
            400: "Bad Request - Profile not found",
            404: "Not Found - Store not found for this user",
        },
        tags=["Store Items"],
    )
    def get(self, request):
        profile_id = get_profile_id_from_token(request)
        if not profile_id:
            return Response(
                {"detail": "Profile not found."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            store = Store.objects.get(profile_id=profile_id)
        except Store.DoesNotExist:
            return Response(
                {"detail": "Store not found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        items = StoreItem.objects.filter(store_id=store)
        serializer = StoreItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)


class StoreItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get store item details",
        description="Retrieve detailed information about a specific store item including inventory and pricing.",
        responses={
            200: StoreItemSerializer,
            401: "Unauthorized - Authentication required",
            404: "Not Found - Item not found",
        },
        tags=["Store Items"],
    )
    def get(self, request, item_id):
        item = get_object_or_404(StoreItem, id=item_id)
        serializer = StoreItemSerializer(item, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update store item",
        description="Fully update a store item. Only the store owner can perform this action.",
        request=StoreItemSerializer,
        responses={
            200: StoreItemSerializer,
            400: "Bad Request - Invalid data",
            403: "Forbidden - Only store owner can update",
            404: "Not Found - Item not found",
        },
        tags=["Store Items"],
    )
    def put(self, request, item_id):
        item = get_object_or_404(StoreItem, id=item_id)
        if not self._is_store_owner_of_item(request, item):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = StoreItemSerializer(
            item, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially update store item",
        description="Partially update a store item. Only the store owner can perform this action.",
        request=StoreItemSerializer,
        responses={
            200: StoreItemSerializer,
            400: "Bad Request - Invalid data",
            403: "Forbidden - Only store owner can update",
            404: "Not Found - Item not found",
        },
        tags=["Store Items"],
    )
    def patch(self, request, item_id):
        item = get_object_or_404(StoreItem, id=item_id)
        if not self._is_store_owner_of_item(request, item):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = StoreItemSerializer(
            item, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete store item",
        description="Delete a store item (only by store owner)",
        responses={204: None},
    )
    def delete(self, request, item_id):
        item = get_object_or_404(StoreItem, id=item_id)
        if not self._is_store_owner_of_item(request, item):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

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
        description="Retrieve orders based on user role and optional filters. Store owners see their orders, buyers see their purchases, admins can filter by profile_id.",
        parameters=[
            OpenApiParameter(
                name="profile_id",
                type=OpenApiTypes.INT,
                description="Filter orders for a specific store by profile ID (admin use)",
                required=False,
            ),
            OpenApiParameter(
                name="buyer_id",
                type=OpenApiTypes.INT,
                description="Filter orders by buyer ID",
                required=False,
            ),
        ],
        responses={
            200: OrderSerializer(many=True),
            401: "Unauthorized - Authentication required",
        },
        tags=["Orders"],
    )
    def get(self, request):
        """
        Query parameters:
        - profile_id: Filter orders for a specific store by profile_id
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

        # Filter by profile_id if provided (for admin or specific queries)
        query_profile_id = request.query_params.get("profile_id")
        if query_profile_id:
            stores = Store.objects.filter(profile_id=query_profile_id)
            if stores.exists():
                orders = orders.filter(store_id__in=stores)

        # Filter by buyer_id if provided
        buyer_id = request.query_params.get("buyer_id")
        if buyer_id:
            orders = orders.filter(buyer_id=buyer_id)

        # If user is authenticated but not a store owner, show their own orders
        if request.user and request.user.is_authenticated and not profile_id:
            orders = orders.filter(buyer_id=request.user.id)

        serializer = OrderSerializer(orders, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create order",
        description="Create a new order. The buyer is set from the authenticated user, and profile_id specifies the store.",
        request=OrderSerializer,
        responses={
            201: OrderSerializer,
            400: "Bad Request - Invalid data or missing profile_id",
            401: "Unauthorized - Authentication required",
        },
        tags=["Orders"],
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
        description="Retrieve detailed information about a specific order including all order items. Only accessible by store owner or buyer.",
        responses={
            200: OrderSerializer,
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Only store owner or buyer can view",
            404: "Not Found - Order not found",
        },
        tags=["Orders"],
    )
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update order",
        description="Fully update an order. Only store owner or buyer can perform this action.",
        request=OrderSerializer,
        responses={
            200: OrderSerializer,
            400: "Bad Request - Invalid data",
            403: "Forbidden - Only store owner or buyer can update",
            404: "Not Found - Order not found",
        },
        tags=["Orders"],
    )
    def put(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not self._can_edit_order(request, order):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = OrderSerializer(
            order, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            order.calculate_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially update order",
        description="Partially update an order. Only store owner or buyer can perform this action.",
        request=OrderSerializer,
        responses={200: OrderSerializer},
    )
    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not self._can_edit_order(request, order):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = OrderSerializer(
            order, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            order.calculate_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete order",
        description="Delete an order (store owner only)",
        responses={204: None},
    )
    def delete(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not self._can_delete_order(request, order):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

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
        description="Retrieve all order items for a specific order. Only accessible by store owner or buyer of the order.",
        responses={
            200: OrderItemSerializer(many=True),
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Only store owner or buyer can view",
            404: "Not Found - Order not found",
        },
        tags=["Order Items"],
    )
    def get(self, request, order_id):
        # Get the specific order
        order = get_object_or_404(Order, id=order_id)

        # Check permissions: store owner or buyer
        profile_id = get_profile_id_from_token(request)
        is_store_owner = order.store_id.profile_id.id == profile_id
        is_buyer = order.buyer_id.id == request.user.id

        if not (is_store_owner or is_buyer):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        # Get items for this order
        items = OrderItem.objects.filter(order_id=order)
        serializer = OrderItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Add item to order",
        description="Add an item to an existing order. Only store owner or buyer can perform this action.",
        request=AddOrderItemSerializer,
        responses={
            201: OrderItemSerializer,
            400: "Bad Request - Invalid data or insufficient inventory",
            403: "Forbidden - Only store owner or buyer can add items",
            404: "Not Found - Order or item not found",
        },
        tags=["Order Items"],
    )
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        # Check permission: store owner or buyer
        if not self._can_edit_order_items(request, order):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddOrderItemSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            store_item_id = serializer.validated_data["store_item_id"]
            size_id = serializer.validated_data.get("size_id")
            quantity = serializer.validated_data["quantity"]

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
                price_at_order=item.price,
            )
            order.calculate_total()

            item_serializer = OrderItemSerializer(
                order_item, context={"request": request}
            )
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
        description="Retrieve details of a specific order item. Only accessible by store owner or buyer of the order.",
        responses={
            200: OrderItemSerializer,
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Only store owner or buyer can view",
            404: "Not Found - Order item not found",
        },
        tags=["Order Items"],
    )
    def get(self, request, order_item_id):
        item = get_object_or_404(OrderItem, id=order_item_id)
        serializer = OrderItemSerializer(item, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Delete order item",
        description="Remove an item from an order. Only store owner or buyer can perform this action.",
        responses={
            204: "No Content - Item deleted successfully",
            403: "Forbidden - Only store owner or buyer can delete",
            404: "Not Found - Order item not found",
        },
        tags=["Order Items"],
    )
    def delete(self, request, order_item_id):
        item = get_object_or_404(OrderItem, id=order_item_id)

        order = item.order_id
        if not self._can_delete_item(request, order):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

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
        description="Update an order item (quantity, etc.). Only store owner or buyer can perform this action.",
        request=OrderItemSerializer,
        responses={
            200: OrderItemSerializer,
            400: "Bad Request - Invalid data",
            403: "Forbidden - Only store owner or buyer can update",
            404: "Not Found - Order item not found",
        },
        tags=["Order Items"],
    )
    def patch(self, request, order_item_id):
        item = get_object_or_404(OrderItem, id=order_item_id)
        order = item.order_id

        if not self._can_delete_item(request, order):
            return Response(
                {"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = OrderItemSerializer(
            item, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            order.calculate_total()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
