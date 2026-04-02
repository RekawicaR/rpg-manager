from django.urls import path
from .views import CampaignCreateView, CampaignListView, CampaignAcceptInviteView, CampaignInviteView, CampaignDetailView, CampaignSourcesView, CampaignItemRuleListCreateView, CampaignItemRuleDeleteView

urlpatterns = [
    path("", CampaignListView.as_view()),
    path("create/", CampaignCreateView.as_view()),
    path("<int:campaign_id>/invite/", CampaignInviteView.as_view(),
         name="campaign-invite-create"),
    path("invites/<uuid:token>/accept/",
         CampaignAcceptInviteView.as_view(), name="campaign-invite-accept"),
    path("<int:campaign_id>/", CampaignDetailView.as_view()),
    path("<int:campaign_id>/sources/", CampaignSourcesView.as_view()),
    path("<int:campaign_id>/rules/", CampaignItemRuleListCreateView.as_view()),
    path("<int:campaign_id>/rules/<int:rule_id>/",
         CampaignItemRuleDeleteView.as_view()),
]
