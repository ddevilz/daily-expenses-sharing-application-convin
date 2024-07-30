from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, ExpenseViewSet, RegisterView, LoginView

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'expenses', ExpenseViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user-expenses/', ExpenseViewSet.as_view({'get': 'user_expenses'}), name='user-expenses'),
    path('overall-expenses/', ExpenseViewSet.as_view({'get': 'overall_expenses'}), name='overall-expenses'),
    path('download-balance-sheet/', ExpenseViewSet.as_view({'get': 'download_balance_sheet'}), name='download-balance-sheet'),
    path('', include(router.urls)),
]
