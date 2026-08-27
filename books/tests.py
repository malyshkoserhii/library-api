from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer  # <-- Виправлений імпорт

BOOKS_URL = reverse("books:book-list")


def detail_url(book_id: int) -> str:
    return reverse("books:book-detail", args=[book_id])


def sample_book(**params) -> Book:
    defaults = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "cover": "HARD",
        "inventory": 5,
        "daily_fee": Decimal("1.50"),
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_books_allowed(self):
        """Test that unauthenticated users can list books."""
        sample_book()
        sample_book(title="Refactoring")

        res = self.client.get(BOOKS_URL)
        books = Book.objects.all().order_by("id")
        serializer = BookSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Якщо ввімкнена пагінація, перевіряємо через results
        if "results" in res.data:
            self.assertEqual(res.data["results"], serializer.data)
        else:
            self.assertEqual(res.data, serializer.data)

    def test_retrieve_book_detail_allowed(self):
        """Test that unauthenticated users can view book details."""
        book = sample_book()
        res = self.client.get(detail_url(book.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], book.title)

    def test_create_book_forbidden(self):
        """Test that unauthenticated users cannot create books."""
        payload = {
            "title": "New Book",
            "author": "Unknown Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": "2.00",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.client.force_authenticate(self.user)

    def test_create_book_forbidden_for_regular_user(self):
        """Test that non-admin authenticated users cannot create books."""
        payload = {
            "title": "New Book",
            "author": "Unknown Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": "2.00",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_book_forbidden_for_regular_user(self):
        """Test that non-admin authenticated users cannot update books."""
        book = sample_book()
        payload = {"title": "Updated Title"}
        res = self.client.patch(detail_url(book.id), payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_book_forbidden_for_regular_user(self):
        """Test that non-admin authenticated users cannot delete books."""
        book = sample_book()
        res = self.client.delete(detail_url(book.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpassword123",
        )
        self.client.force_authenticate(self.admin)

    def test_create_book_success(self):
        """Test that admin users can create a new book."""
        payload = {
            "title": "Design Patterns",
            "author": "Gang of Four",
            "cover": "HARD",
            "inventory": 8,
            "daily_fee": "3.50",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        book = Book.objects.get(id=res.data["id"])
        for key, value in payload.items():
            if key == "daily_fee":
                self.assertEqual(getattr(book, key), Decimal(value))
            else:
                self.assertEqual(getattr(book, key), value)

    def test_update_book_success(self):
        """Test that admin users can update an existing book."""
        book = sample_book()
        payload = {"inventory": 20}
        res = self.client.patch(detail_url(book.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.inventory, 20)

    def test_delete_book_success(self):
        """Test that admin users can delete a book."""
        book = sample_book()
        res = self.client.delete(detail_url(book.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())
