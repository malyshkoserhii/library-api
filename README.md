# Library Service API

A robust, production-ready RESTful API service built with Django REST Framework for managing a library system, book
inventory tracking, borrowings, automated returns, and user authentication.

---

## 🚀 Key Features

* **JWT Authentication:** Secure token-based authentication (Access & Refresh tokens) via
  `djangorestframework-simplejwt`.
* **Custom User Model:** Authentication powered by `email` instead of traditional usernames.
* **Role-Based Access Control:**
    * **Anonymous Users:** Access to register/login endpoints and OpenAPI/Swagger documentation.
    * **Authenticated Users:** Ability to view available books, borrow books, return books, and view personal borrowing
      history.
    * **Admin Staff:** Full CRUD access to manage the book catalog, monitor all user borrowings, and filter borrowings
      across the entire system.
* **Inventory Management & Atomic Operations:**
    * Automated inventory decrements upon book borrowing.
    * Automated inventory increments upon book return.
    * Safe database transactions via `@transaction.atomic` preventing race conditions.
    * Validation barriers preventing borrowing out-of-stock books (`inventory = 0`) or returning an already returned
      book.
* **Database Query Optimization:** Mitigated N+1 query overhead using `select_related` and `prefetch_related` on
  relational models.
* **Filtering & Pagination:**
    * Filter borrowings by status (`is_active=true/false`).
    * Filter borrowings by user (`user_id`) available for administrators.
    * Global PageNumber pagination.
* **Interactive API Documentation:** Interactive Swagger UI and Redoc generated dynamically via `drf-spectacular`.
* **Comprehensive Test Suite:** Unit and integration tests covering authentication barriers, CRUD operations, inventory
  management, filtering parameters, and custom actions.

---

## 🛠 Tech Stack

* **Language:** Python 3.12+
* **Framework:** Django & Django REST Framework
* **Auth:** Simple JWT (`djangorestframework-simplejwt`)
* **Documentation:** `drf-spectacular` (OpenAPI 3.0 / Swagger UI / Redoc)
* **Database:** PostgreSQL
* **Containerization:** Docker & Docker Compose
* **Code Quality:** Flake8

---

## 🐳 Getting Started with Docker

### 1. Clone the repository

```bash
git clone [https://github.com/malyshkoserhii/library-api.git](https://github.com/malyshkoserhii/library-api.git)
cd library-api
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```dotenv
SECRET_KEY=your_secret_key_here
DEBUG=True
POSTGRES_PASSWORD=library
POSTGRES_USER=library
POSTGRES_DB=library
POSTGRES_HOST=db
POSTGRES_PORT=5432
PGDATA=/var/lib/postgresql/data
```

### 3. Build and Run Containers

```bash
docker compose up --build
```

The API server will be available at [http://localhost:8000/](http://localhost:8000/).

---

## ⚙️ Initial Setup

### Apply Migrations

```bash
docker compose exec app python manage.py migrate
```

### Create a Superuser

```bash
docker compose exec app python manage.py createsuperuser
```

---

## 📚 API Endpoints

### Authentication & User Management

| Method  | Endpoint                   | Description                              | Roles         |
|:--------|:---------------------------|:-----------------------------------------|:--------------|
| `POST`  | `/api/user/register/`      | Register a new user                      | Public        |
| `POST`  | `/api/user/token/`         | Obtain JWT access and refresh token pair | Public        |
| `POST`  | `/api/user/token/refresh/` | Refresh JWT access token                 | Public        |
| `POST`  | `/api/user/token/verify/`  | Verify token validity                    | Public        |
| `GET`   | `/api/user/me/`            | Retrieve current user profile            | Authenticated |
| `PATCH` | `/api/user/me/`            | Update current user profile              | Authenticated |

### Books Management

| Method          | Endpoint           | Description                          | Roles                  |
|:----------------|:-------------------|:-------------------------------------|:-----------------------|
| `GET`           | `/api/books/`      | List all books (supports pagination) | Public / Authenticated |
| `POST`          | `/api/books/`      | Add a new book to the catalog        | Admin                  |
| `GET`           | `/api/books/{id}/` | Retrieve detailed book information   | Public / Authenticated |
| `PUT` / `PATCH` | `/api/books/{id}/` | Update book details and inventory    | Admin                  |
| `DELETE`        | `/api/books/{id}/` | Delete a book                        | Admin                  |

### Borrowings Management

| Method | Endpoint                       | Description                                       | Roles                         |
|:-------|:-------------------------------|:--------------------------------------------------|:------------------------------|
| `GET`  | `/api/borrowings/`             | List borrowings (User sees own; Admin sees all)   | Authenticated                 |
| `POST` | `/api/borrowings/`             | Create a new borrowing (decreases book inventory) | Authenticated                 |
| `GET`  | `/api/borrowings/{id}/`        | Retrieve borrowing details                        | Authenticated (Owner / Admin) |
| `POST` | `/api/borrowings/{id}/return/` | Return a borrowed book (increases book inventory) | Authenticated (Owner / Admin) |

---

## 🔍 Query Parameters & Filtering

* **Filter active (not returned yet) borrowings:** `GET /api/borrowings/?is_active=true`
* **Filter returned borrowings:** `GET /api/borrowings/?is_active=false`
* **Filter borrowings by user ID (Admin only):** `GET /api/borrowings/?user_id=2`
* **Combined filtering (Admin only):** `GET /api/borrowings/?is_active=true&user_id=2`
* **Pagination navigation:** `GET /api/borrowings/?page=2`

---

## 📖 API Documentation

Once the server is running, explore and test the endpoints directly in the browser:

* **Swagger UI:** [http://localhost:8000/api/doc/swagger/](http://localhost:8000/api/doc/swagger/)
* **Redoc:** [http://localhost:8000/api/doc/redoc/](http://localhost:8000/api/doc/redoc/)
* **Raw OpenAPI Schema:** [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

---

## 🧪 Testing & Code Quality

### Run Automated Tests

```bash
docker compose run --rm app python manage.py test
```

### Run Flake8 Linter

```bash
docker compose run --rm app flake8
```
