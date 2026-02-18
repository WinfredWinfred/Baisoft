# Baisoft Marketplace API Documentation

## Base URL

```
http://localhost:8000/api
```

## Authentication

All endpoints (except public products) require JWT token in the `Authorization` header:

```
Authorization: Bearer {access_token}
```

---

## 🔐 Authentication Endpoints

### 1. Login (Get JWT Token)

```
POST /auth/login/
```

**Request:**

```json
{
  "username": "admin_user",
  "password": "testpass123"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Get Current User Info

```
GET /auth/me/
```

**Headers:** `Authorization: Bearer {token}`

**Response:**

```json
{
  "id": 1,
  "username": "admin_user",
  "email": "admin@test.com",
  "role": "admin",
  "business": {
    "id": 1,
    "name": "Test Business",
    "description": "Test business for development",
    "user_count": 4
  },
  "is_active": true,
  "date_joined": "2026-02-17T10:30:00Z"
}
```

---

## 📦 Products Endpoints

### 3. List Approved Products (Public)

```
GET /products/public/
```

**Description:** Anyone can access. Returns only approved products.

**Response:**

```json
[
  {
    "id": 1,
    "name": "Laptop",
    "description": "High-performance laptop for professionals",
    "price": "999.99",
    "status": "approved",
    "business": {
      "id": 1,
      "name": "Test Business"
    },
    "created_by": {
      "id": 1,
      "username": "admin_user",
      "role": "admin"
    },
    "created_at": "2026-02-17T10:30:00Z",
    "updated_at": "2026-02-17T10:30:00Z"
  }
]
```

### 4. List All Products (Internal)

```
GET /products/internal/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Authenticated users see all products in their business.

- Admins/Editors/Approvers see all products
- Returns draft, pending_approval, and approved products

**Response:** Same structure as public products list

### 5. Create Product

```
POST /products/internal/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Create a new product (Admin/Editor only)

- Products start in 'draft' status
- Product automatically assigned to user's business

**Request:**

```json
{
  "name": "Monitor",
  "description": "4K monitor for professional work",
  "price": "399.99"
}
```

**Response:** 201 Created

```json
{
  "id": 5,
  "name": "Monitor",
  "description": "4K monitor for professional work",
  "price": "399.99",
  "status": "draft",
  "business": {
    "id": 1,
    "name": "Test Business"
  },
  "created_by": {
    "id": 2,
    "username": "admin_user",
    "role": "admin"
  },
  "created_at": "2026-02-17T11:00:00Z",
  "updated_at": "2026-02-17T11:00:00Z"
}
```

**Authorization:**

- ✅ Admin can create
- ✅ Editor can create
- ❌ Approver cannot create
- ❌ Viewer cannot create

**Error Responses:**

```
403 Forbidden - Only admin or editor users can create products.
400 Bad Request - You must be assigned to a business to create products.
```

### 6. Get Product Details

```
GET /products/<id>/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Get details of a specific product

**Response:** Single product object (same as create response)

**Authorization:** User must have the same business as the product

**Error Responses:**

```
404 Not Found - Product not found
403 Forbidden - This product does not belong to your business.
```

### 7. Update Product

```
PUT /products/<id>/
PATCH /products/<id>/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Update an existing product (Admin/Creator only)

**Request:**

```json
{
  "name": "Updated Monitor",
  "description": "Updated description",
  "price": "449.99",
  "status": "pending_approval"
}
```

**Response:** 200 OK with updated product

**Authorization Rules:**

- ✅ Admin can update any product in their business
- ✅ Editor can update only their own products
- ✅ Admin can change status; Editor cannot
- ❌ Other roles cannot update

**Error Responses:**

```
403 Forbidden - You can only edit or delete your own products.
403 Forbidden - This product does not belong to your business.
404 Not Found - Product not found
```

### 8. Delete Product

```
DELETE /products/<id>/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Delete a product permanently

**Response:** 204 No Content

**Authorization Rules:**

- ✅ Admin can delete any product in their business
- ✅ Creator can delete their own product
- ❌ Other roles cannot delete

**Error Responses:**

```
403 Forbidden - You can only delete your own products.
403 Forbidden - This product does not belong to your business.
404 Not Found - Product not found
```

### 9. Approve Product

```
POST /products/<id>/approve/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Approve a product and make it visible to the public

**Response:** 200 OK

```json
{
  "detail": "Product approved successfully and is now visible to the public.",
  "product": {
    "id": 3,
    "name": "Tablet",
    "status": "approved",
    ...
  }
}
```

**Authorization:**

- ✅ Admin can approve
- ✅ Approver can approve
- ❌ Editor cannot approve
- ❌ Viewer cannot approve

**Error Responses:**

```
403 Forbidden - Only admin or approver users can approve products.
403 Forbidden - This product does not belong to your business.
404 Not Found - Product not found
400 Bad Request - This product is already approved.
```

---

## 👥 User Management Endpoints

### 10. Get Business Info

```
GET /business/me/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Get current user's business information

**Response:**

```json
{
  "id": 1,
  "name": "Test Business",
  "description": "Test business for development",
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "user_count": 4
}
```

### 11. List Business Users

```
GET /business/users/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** List all users in the business (Admin only)

**Response:**

```json
[
  {
    "id": 1,
    "username": "admin_user",
    "email": "admin@test.com",
    "role": "admin",
    "is_active": true,
    "date_joined": "2026-02-17T10:30:00Z"
  },
  {
    "id": 2,
    "username": "editor_user",
    "email": "editor@test.com",
    "role": "editor",
    "is_active": true,
    "date_joined": "2026-02-17T10:31:00Z"
  }
]
```

**Authorization:**

- ✅ Admin can list users
- ❌ Other roles cannot list users

**Error Responses:**

```
403 Forbidden - Only business administrators can perform this action.
```

### 12. Create New User

```
POST /business/users/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Create a new user in the business (Admin only)

**Request:**

```json
{
  "username": "new_editor",
  "email": "neweditor@company.com",
  "password": "secure123",
  "role": "editor",
  "is_active": true
}
```

**Response:** 201 Created

```json
{
  "id": 5,
  "username": "new_editor",
  "email": "neweditor@company.com",
  "role": "editor",
  "is_active": true,
  "date_joined": "2026-02-17T11:15:00Z"
}
```

**Authorization:**

- ✅ Admin can create users
- ❌ Other roles cannot create users

**Error Responses:**

```
403 Forbidden - Only business administrators can perform this action.
400 Bad Request - Username already exists
```

### 13. Get User Details

```
GET /business/users/<id>/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Get details of a specific user (Admin only)

**Response:** Single user object

**Authorization:**

- ✅ Admin can view user details
- ❌ Other roles cannot view

**Error Responses:**

```
403 Forbidden - Only business administrators can perform this action.
404 Not Found - User not found
```

### 14. Update User

```
PUT /business/users/<id>/
PATCH /business/users/<id>/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Update user role and permissions (Admin only)

**Request:**

```json
{
  "role": "approver",
  "is_active": true
}
```

**Response:** 200 OK with updated user

**Authorization:**

- ✅ Admin can update users
- ❌ Other roles cannot update users

**Error Responses:**

```
403 Forbidden - Only business administrators can perform this action.
404 Not Found - User not found
```

### 15. Delete User

```
DELETE /business/users/<id>/
```

**Headers:** `Authorization: Bearer {token}`

**Description:** Remove a user from the business (Admin only)

**Response:** 204 No Content

**Authorization:**

- ✅ Admin can delete users
- ❌ Other roles cannot delete users

**Error Responses:**

```
403 Forbidden - Only business administrators can perform this action.
404 Not Found - User not found
```

---

## 📊 Role Permissions Summary

| Endpoint               | Admin  | Editor | Approver | Viewer |
| ---------------------- | ------ | ------ | -------- | ------ |
| Create Product         | ✅     | ✅     | ❌       | ❌     |
| Update Product         | ✅ All | ✅ Own | ❌       | ❌     |
| Delete Product         | ✅ All | ✅ Own | ❌       | ❌     |
| Approve Product        | ✅     | ❌     | ✅       | ❌     |
| View Internal Products | ✅     | ✅     | ✅       | ❌     |
| View Public Products   | ✅     | ✅     | ✅       | ✅     |
| List Users             | ✅     | ❌     | ❌       | ❌     |
| Create User            | ✅     | ❌     | ❌       | ❌     |
| Update User            | ✅     | ❌     | ❌       | ❌     |
| Delete User            | ✅     | ❌     | ❌       | ❌     |

---

## 🧪 Test Data

Default test users created by `python manage.py seed_testdata`:

| Username      | Password    | Role     | Purpose                         |
| ------------- | ----------- | -------- | ------------------------------- |
| admin_user    | testpass123 | Admin    | Full access to all features     |
| editor_user   | testpass123 | Editor   | Can create/edit products        |
| approver_user | testpass123 | Approver | Can approve products            |
| viewer_user   | testpass123 | Viewer   | Can view approved products only |

Default test products:

- Laptop (Approved)
- Smartphone (Approved)
- Tablet (Pending Approval)
- Monitor (Draft)

---

## 🔄 Common Workflows

### Workflow 1: Create and Approve Product

1. **Editor creates product:**

   ```bash
   POST /products/internal/
   # Returns product with status='draft'
   ```

2. **Editor updates product to pending:**

   ```bash
   PATCH /products/{id}/
   {"status": "pending_approval"}
   ```

3. **Approver approves product:**

   ```bash
   POST /products/{id}/approve/
   # Product status changed to 'approved'
   ```

4. **Public can now see it:**
   ```bash
   GET /products/public/
   # Product appears in list
   ```

### Workflow 2: Manage Team Users

1. **Admin creates new user:**

   ```bash
   POST /business/users/
   {"username": "newuser", "email": "...", "password": "...", "role": "editor"}
   ```

2. **Admin updates user role:**

   ```bash
   PATCH /business/users/{id}/
   {"role": "approver"}
   ```

3. **Admin removes user:**
   ```bash
   DELETE /business/users/{id}/
   ```

---

## ⚠️ Status Codes

| Code | Meaning                    |
| ---- | -------------------------- |
| 200  | Success                    |
| 201  | Created                    |
| 204  | No Content (Deleted)       |
| 400  | Bad Request (Invalid data) |
| 403  | Forbidden (No permission)  |
| 404  | Not Found                  |
| 500  | Server Error               |

---

## 🚀 Getting Started

1. **Start Django server:**

   ```bash
   python manage.py runserver
   ```

2. **Login to get token:**

   ```bash
   curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username": "admin_user", "password": "testpass123"}'
   ```

3. **Use token in requests:**
   ```bash
   curl http://localhost:8000/api/business/users/ \
     -H "Authorization: Bearer {access_token}"
   ```
