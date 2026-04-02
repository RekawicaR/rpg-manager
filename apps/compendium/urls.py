from rest_framework.routers import DefaultRouter
from apps.compendium.views.spell import SpellViewSet

router = DefaultRouter()
router.register("", SpellViewSet, basename="spells")

urlpatterns = router.urls
