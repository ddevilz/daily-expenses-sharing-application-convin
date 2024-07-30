from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Expense, ExpenseParticipant

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CustomUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'mobile_number']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['password'] = validated_data.pop('password')
        user = User.objects.create_user(**user_data)
        custom_user = CustomUser.objects.create(user=user, **validated_data)
        return custom_user

class ExpenseParticipantSerializer(serializers.ModelSerializer):
    participant = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    
    class Meta:
        model = ExpenseParticipant
        fields = ['participant', 'amount_owed', 'percentage_owed']

class ExpenseSerializer(serializers.ModelSerializer):
    payer = CustomUserSerializer(read_only=True)
    participants = ExpenseParticipantSerializer(source='expenseparticipant_set', many=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'title', 'amount', 'date', 'split_method', 'payer', 'participants']

    def create(self, validated_data):
        participants_data = validated_data.pop('expenseparticipant_set')
        expense = Expense.objects.create(**validated_data)
        
        for participant_data in participants_data:
            ExpenseParticipant.objects.create(expense=expense, **participant_data)
        
        expense.calculate_splits()
        return expense

    def update(self, instance, validated_data):
        participants_data = validated_data.pop('expenseparticipant_set', None)
        
        instance = super().update(instance, validated_data)
        
        if participants_data:
            # If there are new participant data, update them
            instance.expenseparticipant_set.all().delete()
            for participant_data in participants_data:
                ExpenseParticipant.objects.create(expense=instance, **participant_data)
        
        instance.calculate_splits()
        return instance

    def validate(self, data):
        split_method = data['split_method']
        participants = data['expenseparticipant_set']
        
        if split_method == 'EQUAL':
            for participant in participants:
                if 'amount_owed' in participant or 'percentage_owed' in participant:
                    raise serializers.ValidationError("Equal split should not have amount or percentage specified.")
        
        elif split_method == 'EXACT':
            total_amount = sum(participant.get('amount_owed', 0) for participant in participants)
            if total_amount != data['amount']:
                raise serializers.ValidationError("Sum of exact amounts must equal the total expense amount.")
        
        elif split_method == 'PERCENTAGE':
            total_percentage = sum(participant.get('percentage_owed', 0) for participant in participants)
            if total_percentage != 100:
                raise serializers.ValidationError("Sum of percentages must equal 100%.")
        
        return data