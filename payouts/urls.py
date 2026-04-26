from django.urls import path
from .views import PayoutCreateView, PayoutListView

urlpatterns = [
    path('payouts/', PayoutCreateView.as_view(), name='payout-create'),
    path('payouts/list/', PayoutListView.as_view(), name='payout-list'),
]