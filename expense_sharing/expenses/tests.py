from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth.models import User

class ExpenseTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_create_user(self):
        url = reverse('register')
        data = {'username': 'newuser', 'email': 'newuser@example.com', 'password': 'password'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_expense(self):
        self.client.login(username='testuser', password='password')
        url = reverse('add-expense')
        data = {
            'description': 'Dinner',
            'total_amount': 100.0,
            'split_method': 'equal',
            'users': [
                {'user': self.user.id, 'amount_owed': 50.0},
                {'user': 2, 'amount_owed': 50.0},
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)