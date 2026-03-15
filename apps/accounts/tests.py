from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


User = get_user_model()


class RegisterTests(APITestCase):

    def test_user_can_register(self):
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123"
        }

        response = self.client.post("/api/auth/register/", payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)

        user = User.objects.first()
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, "USER")


class LoginTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123"
        )

    def test_user_can_login(self):
        payload = {
            "username": "testuser",
            "password": "TestPassword123"
        }

        response = self.client.post("/api/auth/login/", payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_wrong_password(self):
        payload = {
            "username": "testuser",
            "password": "WrongPassword123"
        }

        response = self.client.post("/api/auth/login/", payload)
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_wrong_username(self):
        payload = {
            "username": "wronguser",
            "password": "TestPassword123"
        }

        response = self.client.post("/api/auth/login/", payload)
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)


class TokenRefreshTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123"
        )

    def test_refresh_token(self):
        login = self.client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "TestPassword123"
        })

        refresh_token = login.data["refresh"]
        response = self.client.post("/api/auth/refresh/", {
            "refresh": refresh_token
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
