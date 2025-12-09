# Store API - Serializers & Views with Authorization

## Authorization Summary

### Store Management (StoreListView, StoreDetailView)
- **GET /stores/** - Anyone can view all stores
- **POST /stores/** - Only users with "store" profile/group
- **GET /stores/{id}/** - Anyone can view
- **PUT/PATCH /stores/{id}/** - Only store owner
- **DELETE /stores/{id}/** - Only store owner

### Store Items (StoreItemListView, StoreItemDetailView)
- **GET /items/** - Anyone can view items
- **POST /items/** - Only store profile owners can add items
- **GET /items/{id}/** - Anyone can view
- **PUT/PATCH /items/{id}/** - Only item's store owner
- **DELETE /items/{id}/** - Only item's store owner

### Orders (OrderListView, OrderDetailView)
- **GET /orders/** - Anyone can view all orders
- **POST /orders/** - Any authenticated user can create
- **GET /orders/{id}/** - Anyone can view
- **PUT/PATCH /orders/{id}/** - Store owner OR buyer
- **DELETE /orders/{id}/** - Store owner OR buyer

### Order Items (OrderItemListView, OrderItemDetailView)
- **GET /orders/{id}/items/** - Anyone can view
- **POST /orders/{id}/items/** - Store owner OR buyer can add items
- **GET /orders/items/{id}/** - Anyone can view
- **DELETE /orders/items/{id}/** - Store owner OR buyer can delete

---

## Example Payloads

### 1. Create Store
```json
POST /api/stores/

{
    "account_id": 1,
    "name": "FitnessPro Store",
    "profile_picture": "https://...",
    "description": "Premium fitness supplements",
    "store_type": "supplements"
}
```

### 2. Create Store Item
```json
POST /api/stores/items/

{
    "account_id": 1,
    "store_id": 1,
    "name": "Whey Protein 5kg",
    "description": "High-quality whey protein isolate",
    "price": 89.99,
    "category": "supplements",
    "brand": "GymGem",
    "expiration_date": "2026-12-31"
}
```

### 3. Create Order
```json
POST /api/stores/orders/

{
    "account_id": 2,
    "store_id": 1,
    "buyer_id": 2,
    "status": "pending",
    "notes": "Please deliver in the morning"
}
```

Response:
```json
{
    "id": 5,
    "store_id": 1,
    "store_name": "FitnessPro Store",
    "buyer_id": 2,
    "buyer_name": "john_doe",
    "total_price": "0.00",
    "status": "pending",
    "notes": "Please deliver in the morning",
    "order_items": [],
    "created_at": "2025-12-08T...",
    "updated_at": "2025-12-08T..."
}
```

### 4. Add Item to Order
```json
POST /api/stores/orders/5/items/

{
    "store_item_id": 1,
    "quantity": 2,
    "size_id": null
}
```

Response:
```json
{
    "id": 1,
    "store_item_id": 1,
    "store_item_name": "Whey Protein 5kg",
    "size_id": null,
    "size_name": null,
    "quantity": 2,
    "price_at_order": "89.99",
    "created_at": "2025-12-08T..."
}
```

### 5. Update Order Status
```json
PATCH /api/stores/orders/5/

{
    "status": "confirmed"
}
```

### 6. Delete Order Item
```
DELETE /api/stores/orders/items/1/
```

---

## Important Notes

1. **Store Profile Required**: Users must have a "store" profile/group to create stores and items
2. **Authentication**: All write operations require authenticated users
3. **Ownership**: Modifications are restricted to resource owners (store owner or buyer)
4. **Order Total**: Automatically calculated when items are added/deleted
5. **Price Snapshot**: Order items store the price at the time of order creation (price_at_order)

## Headers Required (Authenticated Requests)

```
Authorization: Bearer <YOUR_JWT_TOKEN>
Content-Type: application/json
```

## Permission Flow

**For Store Item Creation:**
1. User must be authenticated ✓
2. User must have "store" group/profile ✓
3. Store must belong to user's store profile ✓

**For Order Creation:**
1. User must be authenticated ✓
2. Buyer ID can be set to current user or provided

**For Order Item Addition:**
1. User must be authenticated ✓
2. Must be either store owner OR order buyer ✓
