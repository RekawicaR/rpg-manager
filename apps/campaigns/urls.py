from django.urls import path
from .views import CampaignCreateView, CampaignListView

urlpatterns = [
    path("", CampaignListView.as_view()),
    path("create/", CampaignCreateView.as_view()),
]
