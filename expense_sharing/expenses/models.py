from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime

class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username

class Expense(models.Model):
    SPLIT_CHOICES = [
        ('EQUAL', 'Equal'),
        ('EXACT', 'Exact'),
        ('PERCENTAGE', 'Percentage'),
    ]

    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=datetime.now)
    split_method = models.CharField(max_length=10, choices=SPLIT_CHOICES)
    payer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='expenses_paid')
    participants = models.ManyToManyField(CustomUser, through='ExpenseParticipant')

    def __str__(self):
        return f"{self.title} - {self.amount}"

    def calculate_splits(self):
        participants = self.expenseparticipant_set.all()
        num_participants = participants.count()

        if self.split_method == 'EQUAL':
            amount_per_person = self.amount / num_participants
            for participant in participants:
                participant.amount_owed = amount_per_person
                participant.save()

        elif self.split_method == 'EXACT':
            total_owed = sum(p.amount_owed for p in participants)
            if total_owed != self.amount:
                raise ValueError("Total of exact amounts does not match the expense total")

        elif self.split_method == 'PERCENTAGE':
            for participant in participants:
                participant.amount_owed = (participant.percentage_owed / Decimal('100')) * self.amount
                participant.save()

        self.save()

class ExpenseParticipant(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    participant = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage_owed = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        unique_together = ('expense', 'participant')

    def __str__(self):
        return f"{self.participant} - {self.expense}"