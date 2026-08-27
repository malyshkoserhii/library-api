from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

REGISTER_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
ME_URL = reverse("user:manage_user")


class PublicUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a new user with valid credentials."""
        payload = {
            "email": "test@example.com",
            "password": "strong_password123",
        }
        res = self.client.post(REGISTER_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_create_user_with_existing_email_fails(self):
        """
        Test that registering with an already existing email
        returns 400 Bad Request.
        """
        payload = {
            "email": "duplicate@example.com",
            "password": "password123",
        }
        get_user_model().objects.create_user(**payload)

        res = self.client.post(REGISTER_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtain_token_success(self):
        """Test obtaining JWT tokens with valid credentials."""
        email = "tokenuser@example.com"
        password = "valid_password123"
        get_user_model().objects.create_user(email=email, password=password)

        payload = {"email": email, "password": password}
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_obtain_token_invalid_credentials_fails(self):
        """Test that token request with invalid credentials returns 401 Unauthorized."""
        payload = {"email": "nonexistent@example.com", "password": "wrongpassword"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cannot_access_profile(self):
        """Test that unauthenticated requests to /me/ return 401 Unauthorized."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="profile_user@example.com",
            password="initial_password123",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving current user's profile."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)
        self.assertNotIn("password", res.data)

    def test_update_profile_password(self):
        """Test updating password updates hash properly."""
        payload = {
            "email": "updated_user@example.com",
            "password": "new_secret_password123",
        }
        res = self.client.patch(ME_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, payload["email"])
        self.assertTrue(self.user.check_password(payload["password"]))
