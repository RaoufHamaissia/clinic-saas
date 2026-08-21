from django.test import TestCase
from django.urls import reverse

from .models import User
# Create your tests here.

class AuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(     #type:ignore
            email="doctor@example.com",
            password="StrongPassword123!",
            first_name="John",
            last_name="Doe",
        )

    def test_login_page_is_accessible(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)

    def test_user_can_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": "doctor@example.com",
                "password": "StrongPassword123!",
            }
        )
        self.assertRedirects(response, reverse("core:dashboard"))

        

        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_invalid_password_does_not_login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": "doctor@example.com",
                "password": "WrongPassword123!",
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(response.wsgi_request.user.is_authenticated)



    def test_logout(self):
        self.client.login(
            email="doctor@example.com",
            password="StrongPassword123!",
        )

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("accounts:login"))

        response = self.client.get(reverse("core:dashboard"))

        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')