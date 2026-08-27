from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingDetailSerializer,
    BorrowingListSerializer,
)

BORROWINGS_URL = reverse("borrowings:borrowing-list")


def detail_url(borrowing_id: int) -> str:
    return reverse("borrowings:borrowing-detail", args=[borrowing_id])


def return_url(borrowing_id: int) -> str:
    return reverse("borrowings:borrowing-return-borrowing", args=[borrowing_id])


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


def sample_borrowing(user, book, **params) -> Borrowing:
    defaults = {
        "expected_return_date": date.today() + timedelta(days=7),
        "book": book,
        "user": user,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


class UnauthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access borrowings."""
        res = self.client.get(BORROWINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testpassword123",
        )
        self.client.force_authenticate(self.user)
        self.book = sample_book()

    # --- LIST AND FILTERING TESTS ---

    def test_list_borrowings_limited_to_user(self):
        """Test that non-staff users can only see their own borrowings."""
        sample_borrowing(user=self.user, book=self.book)
        sample_borrowing(user=self.other_user, book=self.book)

        res = self.client.get(BORROWINGS_URL)

        borrowings = Borrowing.objects.filter(user=self.user)
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_borrowings_by_is_active(self):
        """Test filtering borrowings by is_active query parameter."""
        active_borrowing = sample_borrowing(user=self.user, book=self.book)
        returned_borrowing = sample_borrowing(
            user=self.user,
            book=self.book,
            actual_return_date=date.today(),
        )

        res_active = self.client.get(BORROWINGS_URL, {"is_active": "true"})
        res_returned = self.client.get(BORROWINGS_URL, {"is_active": "false"})

        active_serializer = BorrowingListSerializer([active_borrowing], many=True)
        returned_serializer = BorrowingListSerializer([returned_borrowing], many=True)

        self.assertEqual(res_active.status_code, status.HTTP_200_OK)
        self.assertEqual(res_active.data["results"], active_serializer.data)

        self.assertEqual(res_returned.status_code, status.HTTP_200_OK)
        self.assertEqual(res_returned.data["results"], returned_serializer.data)

    def test_retrieve_borrowing_detail(self):
        """Test retrieving a specific borrowing detail."""
        borrowing = sample_borrowing(user=self.user, book=self.book)
        url = detail_url(borrowing.id)

        res = self.client.get(url)
        serializer = BorrowingDetailSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_user_cannot_view_other_user_borrowing_detail(self):
        """Test that a user cannot access details of another user's borrowing."""
        other_borrowing = sample_borrowing(
            user=self.other_user,
            book=self.book,
        )
        url = detail_url(other_borrowing.id)

        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # --- CREATE BORROWING TESTS ---

    def test_create_borrowing_success(self):
        """Test creating a borrowing successfully decreases book inventory by 1."""
        initial_inventory = self.book.inventory
        payload = {
            "book": self.book.id,
            "expected_return_date": (date.today() + timedelta(days=5)).isoformat(),
        }

        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory - 1)

        borrowing = Borrowing.objects.get(id=res.data["id"])
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, self.book)

    def test_create_borrowing_with_zero_inventory_fails(self):
        """
        Test creating a borrowing for a book with 0 inventory
        returns 400 Bad Request.
        """
        empty_book = sample_book(title="Empty Book", inventory=0)
        payload = {
            "book": empty_book.id,
            "expected_return_date": (date.today() + timedelta(days=3)).isoformat(),
        }

        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book", res.data)

    # --- RETURN BORROWING TESTS ---

    def test_return_borrowing_success(self):
        """
        Test returning a borrowing sets actual_return_date
        and increments book inventory.
        """
        borrowing = sample_borrowing(user=self.user, book=self.book)
        initial_inventory = self.book.inventory
        url = return_url(borrowing.id)

        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(borrowing.actual_return_date, date.today())
        self.assertEqual(self.book.inventory, initial_inventory + 1)

    def test_return_borrowing_twice_fails(self):
        """Test returning an already returned borrowing returns 400 Bad Request."""
        borrowing = sample_borrowing(
            user=self.user,
            book=self.book,
            actual_return_date=date.today(),
        )
        url = return_url(borrowing.id)

        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res.data["detail"],
            "This borrowing has already been returned.",
        )


class AdminBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpassword123",
        )
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.client.force_authenticate(self.admin)
        self.book = sample_book()

    def test_admin_can_see_all_borrowings(self):
        """Test that admin users can view borrowings of all users."""
        sample_borrowing(user=self.admin, book=self.book)
        sample_borrowing(user=self.user, book=self.book)

        res = self.client.get(BORROWINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 2)

    def test_admin_filter_by_user_id(self):
        """Test that admin users can filter borrowings by a specific user_id."""
        sample_borrowing(user=self.admin, book=self.book)
        user_borrowing = sample_borrowing(user=self.user, book=self.book)

        res = self.client.get(BORROWINGS_URL, {"user_id": self.user.id})

        serializer = BorrowingListSerializer([user_borrowing], many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)
