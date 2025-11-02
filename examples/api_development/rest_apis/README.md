# REST API Development Example

## 🎯 Scenario

Create a complete REST API application with:
- FastAPI/Flask with modern async support
- Database models with SQLAlchemy
- Authentication and authorization
- API documentation with OpenAPI/Swagger
- Request validation and error handling
- Pagination and filtering
- Rate limiting and caching
- Testing framework
- Docker deployment

## 🚀 Quick Start

```bash
# Navigate to this directory
cd examples/api_development/rest_apis

# Create the complete REST API
clippy "Create a complete REST API using FastAPI with SQLAlchemy, authentication, OpenAPI docs, request validation, pagination, rate limiting, testing, and Docker deployment"
```

## 📁 Expected Project Structure

```
rest_apis/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Configuration
│   │   │   ├── security.py         # Authentication
│   │   │   ├── database.py         # Database setup
│   │   │   └── dependencies.py     # FastAPI dependencies
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User model
│   │   │   ├── product.py          # Product model
│   │   │   └── order.py            # Order model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User schemas
│   │   │   ├── product.py          # Product schemas
│   │   │   └── order.py            # Order schemas
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # API dependencies
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── endpoints/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── users.py    # User endpoints
│   │   │       │   ├── products.py # Product endpoints
│   │   │       │   ├── orders.py   # Order endpoints
│   │   │       │   └── auth.py     # Authentication endpoints
│   │   │       └── api.py          # API router
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py     # User business logic
│   │   │   ├── product_service.py  # Product business logic
│   │   │   └── order_service.py    # Order business logic
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── pagination.py       # Pagination utilities
│   │       ├── filtering.py        # Query filtering
│   │       └── cache.py            # Caching utilities
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # Test configuration
│   │   ├── test_auth.py            # Authentication tests
│   │   ├── test_users.py           # User API tests
│   │   ├── test_products.py        # Product API tests
│   │   └── test_orders.py          # Order API tests
│   ├── pyproject.toml              # Modern API packaging with uv
│   └── Dockerfile                  # Docker setup
├── scripts/
│   ├── init_db.py                  # Database initialization
│   ├── seed_data.py                # Sample data
│   └── migrate.py                  # Database migrations
├── docker-compose.yml              # Development environment
├── docker-compose.prod.yml         # Production environment
├── .env.example                    # Environment variables
├── .gitignore
├── README.md                       # This file
└── alembic.ini                     # Alembic configuration
```

## 🛠️ Step-by-Step Commands

### 1. Create FastAPI Project Structure
```bash
clippy "Create FastAPI project structure with proper separation of models, schemas, services, and API endpoints following best practices"
```

### 2. Setup Database Models
```bash
clippy "Create SQLAlchemy models for User, Product, and Order with relationships, indexes, and proper field types"
```

### 3. Implement Pydantic Schemas
```bash
clippy "Create Pydantic schemas for request/response validation with proper data types, validation rules, and relationships"
```

### 4. Build API Endpoints
```bash
clippy "Create RESTful API endpoints for CRUD operations with proper HTTP status codes, error handling, and response models"
```

### 5. Add Authentication System
```bash
clippy "Implement JWT authentication with password hashing, token refresh, role-based access control, and middleware"
```

### 6. Add Pagination and Filtering
```bash
clippy "Create pagination system with cursor-based pagination, query filtering, sorting, and search functionality"
```

### 7. Implement Rate Limiting and Caching
```bash
clippy "Add rate limiting using slowapi and Redis caching with proper cache invalidation and TTL management"
```

### 8. Create Comprehensive Tests
```bash
clippy "Create pytest tests for all endpoints with fixtures, mocking, and integration tests covering authentication and business logic"
```

## 💡 Advanced Features

### WebSocket Support
```bash
clippy "Add WebSocket endpoints for real-time communication with connection management and authentication"
```

### API Versioning
```bash
clippy "Implement API versioning with proper backward compatibility and deprecation handling"
```

### Background Tasks
```bash
clippy "Add background task processing with Celery and Redis for async operations"
```

## 🔍 API Development Validation

```bash
# ✅ FastAPI application validated
clippy "Create FastAPI app with proper middleware, CORS, and OpenAPI configuration"

# ✅ Pydantic schemas validated
clippy "Create request/response schemas with proper validation and documentation"

# ✅ SQLAlchemy models validated
clippy "Create database models with relationships, indexes, and constraints"
```

## 📝 Example API Development Session

```
$ clippy
> Create a complete REST API using FastAPI with authentication and database

🤖 I'll create a comprehensive REST API with all modern features.

📋 Plan:
1. Set up FastAPI project structure
2. Create database models with SQLAlchemy
3. Implement Pydantic schemas for validation
4. Build RESTful endpoints with CRUD operations
5. Add JWT authentication with role-based access
6. Implement pagination, filtering, and search
7. Add rate limiting and caching
8. Create comprehensive tests
9. Setup Docker deployment

🎯 Setting up project structure...

✅ Successfully created FastAPI application structure
✅ Set up proper imports and module organization
✅ Created configuration management

🤖 Building database models...

✅ Successfully wrote to src/app/models/user.py
✅ Successfully wrote to src/app/models/product.py
✅ Successfully wrote to src/app/models/order.py

🤖 Implementing API endpoints...

✅ Successfully wrote to src/app/api/v1/endpoints/users.py
✅ Successfully wrote to src/app/api/v1/endpoints/products.py
✅ Successfully wrote to src/app/api/v1/endpoints/orders.py

🤖 Adding authentication...

✅ Successfully wrote to src/app/core/security.py
✅ JWT authentication with password hashing and role-based access

🎉 Complete REST API created!
Start: `uvicorn src.app.main:app --reload`
Docs: `http://localhost:8000/docs`
Test: `pytest src/tests/`
```

## 🌐 API Endpoints Documentation

### Authentication Endpoints
```bash
POST /api/v1/auth/login          # User login
POST /api/v1/auth/refresh        # Refresh JWT token
POST /api/v1/auth/register       # User registration
POST /api/v1/auth/logout         # User logout
```

### User Management
```bash
GET    /api/v1/users              # List users (paginated)
GET    /api/v1/users/{user_id}    # Get user details
POST   /api/v1/users              # Create user
PUT    /api/v1/users/{user_id}    # Update user
DELETE /api/v1/users/{user_id}    # Delete user
```

### Product Management
```bash
GET    /api/v1/products           # List products (with filtering)
GET    /api/v1/products/{id}      # Get product details
POST   /api/v1/products           # Create product (admin)
PUT    /api/v1/products/{id}      # Update product
DELETE /api/v1/products/{id}      # Delete product (admin)
```

### Order Management
```bash
GET    /api/v1/orders             # List user orders
GET    /api/v1/orders/{order_id}  # Get order details
POST   /api/v1/orders             # Create order
PUT    /api/v1/orders/{order_id}  # Update order
DELETE /api/v1/orders/{order_id}  # Cancel order
```

## 🔄 Request/Response Examples

### Create User Request
```json
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

### User Response
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Products with Pagination
```json
GET /api/v1/products?page=1&size=20&sort=price&order=desc&category=electronics
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8,
  "has_next": true,
  "has_prev": false
}
```

## 🔐 Authentication Flow

### JWT Token Structure
```python
{
  "sub": "user@example.com",
  "user_id": 1,
  "role": "user",
  "exp": 1642694400,
  "iat": 1642690800
}
```

### Role-Based Access Control
```python
@router.get("/admin/users")
async def get_users(
    current_user: User = Depends(get_current_admin_user)
):
    # Only admin users can access this endpoint
    pass

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    # All authenticated users can access this endpoint
    pass
```

## 📊 Pagination and Filtering

### Query Parameters
```bash
# Pagination
GET /api/v1/products?page=1&size=20

# Sorting
GET /api/v1/products?sort=price&order=desc

# Filtering
GET /api/v1/products?category=electronics&min_price=100&max_price=1000

# Search
GET /api/v1/products?q=laptop&search_fields=name,description
```

### Pagination Response
```python
{
  "items": [...],
  "pagination": {
    "total": 150,
    "page": 1,
    "size": 20,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## 🚀 Rate Limiting Configuration

### Rate Limiting Rules
```python
# Different limits per endpoint
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379"
)

@limiter.limit("100/minute")  # 100 requests per minute
async def get_products():
    pass

@limiter.limit("10/minute")   # Stricter for sensitive operations
async def create_order():
    pass
```

### Rate Limit Response
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "reset_time": "2024-01-15T10:31:00Z"
}
```

## 🗄️ Database Models

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user")
```

### Product Model
```python
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String, index=True)
    stock_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
```

## 🧪 Testing the API

### Running Tests
```bash
# Run all tests
pytest src/tests/ -v

# Run specific test file
pytest src/tests/test_auth.py -v

# Run with coverage
pytest --cov=src/app --cov-report=html

# Run integration tests
pytest src/tests/ -m integration
```

### Test Examples
```python
def test_create_user(client):
    """Test user creation endpoint"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]

def test_login_user(client, test_user):
    """Test user login"""
    login_data = {
        "username": test_user.email,
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## 📝 OpenAPI/Swagger Documentation

### Generated Docs
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Custom Documentation
```python
@router.post(
    "/products/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product. Only admin users can create products.",
    responses={
        201: {"description": "Product created successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - admin access required"}
    }
)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_admin_user)
):
    pass
```

## 🐳 Docker Deployment

### Development Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Docker Compose Development
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/testdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./src:/app/src

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=testdb
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## 🚨 Error Handling

### Standardized Error Responses
```python
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValueError, value_error_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "path": "/api/v1/users"
  }
}
```

## 🔄 Caching Strategy

### Redis Caching
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@router.get("/products/{product_id}")
@cache(expire=60)  # Cache for 60 seconds
async def get_product(product_id: int):
    pass
```

### Cache Invalidation
```python
async def invalidate_product_cache(product_id: int):
    await FastAPICache.clear(namespace=f"product_{product_id}")
```

## 📈 Performance Monitoring

### Request Metrics
```python
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_group_untemplated=True,
    should_instrument_requests_inprogress=True,
    should_instrument_requests_duration=True,
    excluded_handlers=[".*admin.*"],
    env_vars_name_for_prefix="PROMETHEUS_",
    inprogress_name="fastapi_inprogress",
    inprogress_labels=True,
    should_group_status_codes=False,
)

instrumentator.instrument(app).expose(app)
```

## 🔧 Environment Configuration

### Development (.env)
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/devdb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
DEBUG=true
```

### Production (.env.prod)
```bash
DATABASE_URL=postgresql://user:password@postgres:5432/proddb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=${RANDOM_SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
```

## 🎯 Best Practices Demonstrated

- **API Design**: RESTful principles, proper HTTP methods
- **Security**: JWT authentication, role-based access, input validation
- **Performance**: Pagination, caching, rate limiting, async operations
- **Testing**: Comprehensive test coverage, fixtures, integration tests
- **Documentation**: Auto-generated OpenAPI docs, custom documentation
- **Error Handling**: Standardized error responses, proper status codes
- **Scalability**: Database design, caching strategy, Docker deployment
- **Code Quality**: Type hints, separation of concerns, clean architecture

## 🔧 Common API Development Issues

### Authentication Issues
```bash
# Fix JWT token validation
clippy "Debug JWT authentication issues with token expiration and validation"

# Fix role-based access control
clippy "Implement proper role checking and authorization middleware"
```

### Performance Issues
```bash
# Optimize database queries
clippy "Fix N+1 query problems and optimize database performance"

# Add proper indexing
clippy "Add database indexes for commonly queried fields"
```

### Validation Issues
```bash
# Fix request validation
clippy "Implement proper Pydantic models with comprehensive validation rules"

# Handle edge cases
clippy "Add validation for edge cases and malformed input"
```

This comprehensive REST API example demonstrates modern API development with all the features developers expect in production systems! 🚀📎