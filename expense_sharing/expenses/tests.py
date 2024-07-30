from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import CustomUser, Expense

class ExpenseTests(APITestCase):
    def setUp(self):

        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        self.user3 = User.objects.create_user(username='user3', password='password3')

        self.custom_user1 = CustomUser.objects.create(user=self.user1, mobile_number='1234567890')
        self.custom_user2 = CustomUser.objects.create(user=self.user2, mobile_number='2345678901')
        self.custom_user3 = CustomUser.objects.create(user=self.user3, mobile_number='3456789012')

        response = self.client.post(reverse('login'), {'username': 'user1', 'password': 'password1'})
        self.token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

    def test_create_expense_equal_split(self):
        url = reverse('expense-list')
        data = {
            "title": "Dinner",
            "amount": 100.00,
            "date": "2024-07-29",
            "split_method": "EQUAL",
            "participants": [
                {"participant": self.custom_user1.id},
                {"participant": self.custom_user2.id},
                {"participant": self.custom_user3.id}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['split_method'], 'EQUAL')

    def test_create_expense_exact_split(self):
        url = reverse('expense-list')
        data = {
            "title": "Lunch",
            "amount": 90.00,
            "date": "2024-07-29",
            "split_method": "EXACT",
            "participants": [
                {"participant": self.custom_user1.id, "amount_owed": 30.00},
                {"participant": self.custom_user2.id, "amount_owed": 30.00},
                {"participant": self.custom_user3.id, "amount_owed": 30.00}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['split_method'], 'EXACT')

    def test_create_expense_percentage_split(self):
        url = reverse('expense-list')
        data = {
            "title": "Brunch",
            "amount": 200.00,
            "date": "2024-07-29",
            "split_method": "PERCENTAGE",
            "participants": [
                {"participant": self.custom_user1.id, "percentage_owed": 50},
                {"participant": self.custom_user2.id, "percentage_owed": 30},
                {"participant": self.custom_user3.id, "percentage_owed": 20}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['split_method'], 'PERCENTAGE')

    def test_create_expense_equal_split_invalid(self):
        url = reverse('expense-list')
        data = {
            "title": "Dinner",
            "amount": 100.00,
            "date": "2024-07-29",
            "split_method": "EQUAL",
            "participants": [
                {"participant": self.custom_user1.id, "amount_owed": 30.00},
                {"participant": self.custom_user2.id, "percentage_owed": 20},
                {"participant": self.custom_user3.id}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Equal split should not have amount or percentage specified.', response.data['non_field_errors'])

    def test_create_expense_exact_split_invalid(self):
        url = reverse('expense-list')
        data = {
            "title": "Lunch",
            "amount": 90.00,
            "date": "2024-07-29",
            "split_method": "EXACT",
            "participants": [
                {"participant": self.custom_user1.id, "amount_owed": 40.00},
                {"participant": self.custom_user2.id, "amount_owed": 30.00},
                {"participant": self.custom_user3.id, "amount_owed": 30.00}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Sum of exact amounts must equal the total expense amount.', response.data['non_field_errors'])

    def test_create_expense_percentage_split_invalid(self):
        url = reverse('expense-list')
        data = {
            "title": "Brunch",
            "amount": 200.00,
            "date": "2024-07-29",
            "split_method": "PERCENTAGE",
            "participants": [
                {"participant": self.custom_user1.id, "percentage_owed": 60},
                {"participant": self.custom_user2.id, "percentage_owed": 30},
                {"participant": self.custom_user3.id, "percentage_owed": 20}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Sum of percentages must equal 100%.', response.data['non_field_errors'])
