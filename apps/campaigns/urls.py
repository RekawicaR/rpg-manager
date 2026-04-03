from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet,
    CampaignInviteView,
    CampaignAcceptInviteView,
    CampaignSourcesView,
    CampaignRulesListCreateView,
    CampaignRuleDestroyView
)

router = DefaultRouter()
router.register("", CampaignViewSet, basename="campaigns")

urlpatterns = router.urls + [
    path("<int:campaign_id>/invite/", CampaignInviteView.as_view(), name="campaign-invite-create"),
    path("invites/<uuid:token>/accept/", CampaignAcceptInviteView.as_view(), name="campaign-invite-accept"),
    path("<int:campaign_id>/sources/", CampaignSourcesView.as_view(), name="campaign-sources"),
    path("<int:campaign_id>/rules/", CampaignRulesListCreateView.as_view(), name="campaign-rules"),
    path("<int:campaign_id>/rules/<int:rule_id>/", CampaignRuleDestroyView.as_view(), name="campaign-rule-delete"),
]
