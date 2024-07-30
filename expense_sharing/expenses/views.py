from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Sum, F
from django.http import HttpResponse
from .models import CustomUser, Expense, ExpenseParticipant
from .serializers import CustomUserSerializer, ExpenseSerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
import csv

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        try:
            serializer.save(payer=self.request.user.customuser)
        except ValidationError as e:
            raise ValidationError(detail=str(e))

    @action(detail=False, methods=['GET'])
    def user_expenses(self, request):
        user = request.user.customuser
        expenses = Expense.objects.filter(participants=user)
        serializer = self.get_serializer(expenses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def overall_expenses(self, request):
        total_expenses = Expense.objects.aggregate(total=Sum('amount'))
        return Response(total_expenses)

    @action(detail=False, methods=['GET'])
    def user_balance(self, request):
        user = request.user.customuser
        
        paid = Expense.objects.filter(payer=user).aggregate(total=Sum('amount'))['total'] or 0
        owed = ExpenseParticipant.objects.filter(participant=user).aggregate(total=Sum('amount_owed'))['total'] or 0

        balances = ExpenseParticipant.objects.filter(expense__payer=user).exclude(participant=user).values(
            'participant__user__username'
        ).annotate(
            balance=Sum('amount_owed')
        ).union(
            ExpenseParticipant.objects.filter(participant=user).exclude(expense__payer=user).values(
                'expense__payer__user__username'
            ).annotate(
                balance=-Sum('amount_owed')
            )
        )

        return Response({
            'total_paid': paid,
            'total_owed': owed,
            'net_balance': paid - owed,
            'balances_with_others': balances
        })

    @action(detail=False, methods=['GET'])
    def download_balance_sheet(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="balance_sheet.csv"'

        writer = csv.writer(response)
        writer.writerow(['User', 'Total Paid', 'Total Owed', 'Net Balance', 'Balances with Others'])

        users = CustomUser.objects.all()
        for user in users:
            total_paid = Expense.objects.filter(payer=user).aggregate(total=Sum('amount'))['total'] or 0
            total_owed = ExpenseParticipant.objects.filter(participant=user).aggregate(total=Sum('amount_owed'))['total'] or 0
            net_balance = total_paid - total_owed

            balances = ExpenseParticipant.objects.filter(expense__payer=user).exclude(participant=user).values(
                'participant__user__username'
            ).annotate(
                balance=Sum('amount_owed')
            ).union(
                ExpenseParticipant.objects.filter(participant=user).exclude(expense__payer=user).values(
                    'expense__payer__user__username'
                ).annotate(
                    balance=-Sum('amount_owed')
                )
            )

            balances_str = '; '.join([f"{b['participant__user__username']}: {b['balance']}" for b in balances])

            writer.writerow([user.user.username, total_paid, total_owed, net_balance, balances_str])

        return response

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user.user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'email': user.user.email
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.customuser.id,
                'email': user.email
            })
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)