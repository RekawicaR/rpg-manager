from django.urls import path
from .views import CampaignCreateView, CampaignListView, CampaignAcceptInviteView, CampaignInviteView, CampaignDetailView

urlpatterns = [
    path("", CampaignListView.as_view()),
    path("create/", CampaignCreateView.as_view()),
    path("<int:campaign_id>/invite/", CampaignInviteView.as_view(),
         name="campaign-invite-create"),
    path("invites/<uuid:token>/accept/",
         CampaignAcceptInviteView.as_view(), name="campaign-invite-accept"),
    path("<int:pk>/", CampaignDetailView.as_view()),
]
