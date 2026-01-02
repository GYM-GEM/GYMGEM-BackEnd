# GymGem API Documentation

## Overview
This document provides comprehensive documentation for the GymGem Stores API. The API allows management of stores, branches, items, and orders in the GymGem platform.

## Authentication
All endpoints require JWT authentication. Include the token in the `Authorization` header:
```
Authorization: Bearer <your_jwt_token>
```

## Base URL
```
http://localhost:8000/api/stores/
```

## API Endpoints

### Stores

#### 1. List All Stores
- **Endpoint:** `GET /api/stores/`
- **Permissions:** Users with 'store' role only
- **Description:** Retrieve a list of all stores
- **Response:** Array of store objects
- **Status Codes:**
  - 200: Success
  - 403: Forbidden - User does not have 'store' role

#### 2. Create Store
- **Endpoint:** `POST /api/stores/`
- **Permissions:** Users with 'store' role only
- **Description:** Create a new store for the authenticated user
- **Request Body:**
  ```json
  {
    "name": "My Store",
    "description": "Store description",
    "store_type": "online",
    "phone_number": "+1234567890"
  }
  ```
- **Response:** Created store object
- **Status Codes:**
  - 201: Created
  - 400: Bad Request - Invalid data or store already exists
  - 403: Forbidden

#### 3. Get Store Details
- **Endpoint:** `GET /api/stores/<profile_id>/`
- **Permissions:** Authenticated users
- **Description:** Retrieve details of a specific store
- **Response:** Store object with branches
- **Status Codes:**
  - 200: Success
  - 404: Not Found

#### 4. Update Store
- **Endpoint:** `PUT /api/stores/<profile_id>/`
- **Permissions:** Store owner only
- **Description:** Fully update a store
- **Request Body:** Complete store data
- **Response:** Updated store object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 5. Partially Update Store
- **Endpoint:** `PATCH /api/stores/<profile_id>/`
- **Permissions:** Store owner only
- **Description:** Partially update a store
- **Request Body:** Partial store data
- **Response:** Updated store object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 6. Delete Store
- **Endpoint:** `DELETE /api/stores/<profile_id>/`
- **Permissions:** Store owner only
- **Description:** Delete a store
- **Response:** 204 No Content
- **Status Codes:**
  - 204: Success
  - 403: Forbidden
  - 404: Not Found

### Store Branches

#### 7. List My Store Branches
- **Endpoint:** `GET /api/stores/branches/`
- **Permissions:** Users with 'store' role only
- **Description:** Retrieve branches for the authenticated store owner
- **Response:** Array of branch objects
- **Status Codes:**
  - 200: Success
  - 400: Bad Request - Profile not found
  - 403: Forbidden
  - 404: Not Found - Store not found

#### 8. List Store Branches by Profile ID
- **Endpoint:** `GET /api/stores/branches/public/?profile_id=<profile_id>`
- **Permissions:** Authenticated users
- **Description:** Retrieve branches for a store by profile ID
- **Query Parameters:**
  - `profile_id` (required): Profile ID of the store owner
- **Response:** Array of branch objects
- **Status Codes:**
  - 200: Success
  - 400: Bad Request - profile_id required
  - 404: Not Found - Store not found

#### 9. Create Store Branch
- **Endpoint:** `POST /api/stores/branches/`
- **Permissions:** Users with 'store' role only
- **Description:** Create a new branch for the authenticated store owner's store
- **Request Body:**
  ```json
  {
    "opening_time": "09:00:00",
    "closing_time": "18:00:00",
    "country": "USA",
    "state": "CA",
    "street": "123 Main St",
    "zip_code": "12345",
    "phone_number": "+1234567890"
  }
  ```
- **Response:** Created branch object
- **Status Codes:**
  - 201: Created
  - 400: Bad Request
  - 403: Forbidden

#### 10. Get Branch Details
- **Endpoint:** `GET /api/stores/branches/<branch_id>/`
- **Permissions:** Authenticated users
- **Description:** Retrieve details of a specific branch
- **Response:** Branch object
- **Status Codes:**
  - 200: Success
  - 404: Not Found

#### 11. Update Branch
- **Endpoint:** `PUT /api/stores/branches/<branch_id>/`
- **Permissions:** Store owner only
- **Description:** Fully update a branch
- **Request Body:** Complete branch data
- **Response:** Updated branch object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 12. Partially Update Branch
- **Endpoint:** `PATCH /api/stores/branches/<branch_id>/`
- **Permissions:** Store owner only
- **Description:** Partially update a branch
- **Request Body:** Partial branch data
- **Response:** Updated branch object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 13. Delete Branch
- **Endpoint:** `DELETE /api/stores/branches/<branch_id>/`
- **Permissions:** Store owner only
- **Description:** Delete a branch
- **Response:** 204 No Content
- **Status Codes:**
  - 204: Success
  - 403: Forbidden
  - 404: Not Found

### Store Items

#### 14. List Store Items
- **Endpoint:** `GET /api/stores/items/`
- **Permissions:** Authenticated users
- **Description:** Retrieve store items with optional filtering
- **Query Parameters:**
  - `store_id`: Filter by store ID
  - `branch_id`: Filter by branch ID
  - `category`: Filter by category (supplements, clothes, foods)
  - `price_min`: Minimum price
  - `price_max`: Maximum price
  - `search`: Search in name, description, brand
  - `ordering`: Order by field (name, price, -name, -price)
- **Response:** Array of item objects
- **Status Codes:** 200: Success

#### 15. List My Store Items
- **Endpoint:** `GET /api/stores/my-items/`
- **Permissions:** Authenticated users
- **Description:** Retrieve items belonging to the authenticated store owner
- **Response:** Array of item objects
- **Status Codes:** 200: Success

#### 16. Create Store Item
- **Endpoint:** `POST /api/stores/items/`
- **Permissions:** Store owner only
- **Description:** Create a new store item
- **Request Body:**
  ```json
  {
    "branch_id": 1,
    "name": "Protein Powder",
    "description": "High quality protein",
    "price": 5000,
    "category": "supplements",
    "brand": "Brand X",
    "inventory": [
      {
        "size_id": 1,
        "quantity": 100
      }
    ]
  }
  ```
- **Response:** Created item object
- **Status Codes:**
  - 201: Created
  - 400: Bad Request
  - 403: Forbidden

#### 17. Get Item Details
- **Endpoint:** `GET /api/stores/items/<item_id>/`
- **Permissions:** Authenticated users
- **Description:** Retrieve details of a specific item
- **Response:** Item object with inventory
- **Status Codes:**
  - 200: Success
  - 404: Not Found

#### 18. Update Item
- **Endpoint:** `PUT /api/stores/items/<item_id>/`
- **Permissions:** Store owner only
- **Description:** Fully update an item
- **Request Body:** Complete item data
- **Response:** Updated item object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 19. Partially Update Item
- **Endpoint:** `PATCH /api/stores/items/<item_id>/`
- **Permissions:** Store owner only
- **Description:** Partially update an item
- **Request Body:** Partial item data
- **Response:** Updated item object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 20. Delete Item
- **Endpoint:** `DELETE /api/stores/items/<item_id>/`
- **Permissions:** Store owner only
- **Description:** Delete an item
- **Response:** 204 No Content
- **Status Codes:**
  - 204: Success
  - 403: Forbidden
  - 404: Not Found

### Orders

#### 21. List Orders
- **Endpoint:** `GET /api/stores/orders/`
- **Permissions:** Authenticated users
- **Description:** Retrieve orders based on user role
- **Query Parameters:**
  - `profile_id`: Filter orders for a specific store (admin use)
  - `buyer_id`: Filter orders by buyer ID
- **Behavior:**
  - Store owners: See their store's orders
  - Buyers: See their own orders
  - Admins: Can filter by profile_id
- **Response:** Array of order objects
- **Status Codes:** 200: Success

#### 22. Create Order
- **Endpoint:** `POST /api/stores/orders/`
- **Permissions:** Authenticated users
- **Description:** Create a new order
- **Request Body:**
  ```json
  {
    "profile_id": 123,
    "status": "pending",
    "notes": "Order notes"
  }
  ```
- **Response:** Created order object
- **Status Codes:**
  - 201: Created
  - 400: Bad Request
  - 401: Unauthorized

#### 23. Get Order Details
- **Endpoint:** `GET /api/stores/orders/<order_id>/`
- **Permissions:** Store owner or buyer of the order
- **Description:** Retrieve details of a specific order
- **Response:** Order object with items
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 24. Update Order
- **Endpoint:** `PUT /api/stores/orders/<order_id>/`
- **Permissions:** Store owner or buyer
- **Description:** Fully update an order
- **Request Body:** Complete order data
- **Response:** Updated order object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 25. Partially Update Order
- **Endpoint:** `PATCH /api/stores/orders/<order_id>/`
- **Permissions:** Store owner or buyer
- **Description:** Partially update an order
- **Request Body:** Partial order data
- **Response:** Updated order object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 26. Delete Order
- **Endpoint:** `DELETE /api/stores/orders/<order_id>/`
- **Permissions:** Store owner or buyer
- **Description:** Delete an order
- **Response:** 204 No Content
- **Status Codes:**
  - 204: Success
  - 403: Forbidden
  - 404: Not Found

### Order Items

#### 27. List Order Items
- **Endpoint:** `GET /api/stores/orders/<order_id>/items/`
- **Permissions:** Store owner or buyer of the order
- **Description:** Retrieve items for a specific order
- **Response:** Array of order item objects
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 28. Add Order Item
- **Endpoint:** `POST /api/stores/orders/<order_id>/items/`
- **Permissions:** Store owner or buyer of the order
- **Description:** Add an item to an existing order
- **Request Body:**
  ```json
  {
    "store_item_id": 1,
    "size_id": 1,
    "quantity": 2
  }
  ```
- **Response:** Created order item object
- **Status Codes:**
  - 201: Created
  - 400: Bad Request
  - 403: Forbidden

#### 29. Update Order Item
- **Endpoint:** `PATCH /api/stores/orders/items/<order_item_id>/`
- **Permissions:** Store owner or buyer
- **Description:** Update an order item
- **Request Body:** Partial order item data
- **Response:** Updated order item object
- **Status Codes:**
  - 200: Success
  - 403: Forbidden
  - 404: Not Found

#### 30. Delete Order Item
- **Endpoint:** `DELETE /api/stores/orders/items/<order_item_id>/`
- **Permissions:** Store owner or buyer
- **Description:** Remove an item from an order
- **Response:** 204 No Content
- **Status Codes:**
  - 204: Success
  - 403: Forbidden
  - 404: Not Found

## Data Models

### Store
```json
{
  "id": 1,
  "name": "Store Name",
  "profile_picture": "url",
  "description": "Description",
  "store_type": "online",
  "branches": [...],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z",
  "phone_number": "+1234567890"
}
```

### StoreBranch
```json
{
  "id": 1,
  "store_id": 1,
  "profile_id": 123,
  "opening_time": "09:00:00",
  "closing_time": "18:00:00",
  "country": "USA",
  "state": "CA",
  "street": "123 Main St",
  "zip_code": "12345",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z",
  "phone_number": "+1234567890"
}
```

### StoreItem
```json
{
  "id": 1,
  "store_id": 1,
  "profile_id": 123,
  "branch_id": 1,
  "name": "Item Name",
  "description": "Description",
  "item_image": "url",
  "price": 5000,
  "category": "supplements",
  "status": "published",
  "brand": "Brand X",
  "expiration_date": "2024-01-01",
  "inventory": [...],
  "total_quantity": 100,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Order
```json
{
  "id": 1,
  "profile_id": 123,
  "store_name": "Store Name",
  "buyer_id": 456,
  "buyer_name": "Buyer Name",
  "total_price": 10000,
  "status": "pending",
  "notes": "Notes",
  "order_items": [...],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

## Error Handling
- **400 Bad Request:** Invalid data or missing required fields
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Insufficient permissions
- **404 Not Found:** Resource not found
- **500 Internal Server Error:** Server error

## Frontend Integration Tips
1. **Authentication:** Always include JWT token in requests
2. **Role-based UI:** Show different features based on user roles
3. **Error Handling:** Implement proper error handling for all status codes
4. **Real-time Updates:** Consider polling for order status changes
5. **Validation:** Validate data before sending requests
6. **Permissions:** Check permissions before displaying action buttons

## Swagger Documentation
Access the interactive API documentation at:
```
http://localhost:8000/api/schema/swagger-ui/
```

## Notes
- Prices are in cents (e.g., 5000 = $50.00)
- Total prices in orders are converted to gems (1 USD = 10 gems)
- All times are in 24-hour format
- Authentication is required for all endpoints</content>
<parameter name="filePath">API_DOCUMENTATION.md