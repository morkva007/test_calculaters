from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views import (
    CalculaterViewSet,
    S_directory_DCreativeViewSet,
    AuditoriesViewSet,
    ChangeAuditoriesViewSet,
    ServiceViewSet,
    AccommodationViewSet
)


router = DefaultRouter()
router.register('creative', S_directory_DCreativeViewSet)
router.register('calculaters', CalculaterViewSet)
router.register('auditories', AuditoriesViewSet)
router.register('changea', ChangeAuditoriesViewSet)
router.register('service', ServiceViewSet)
router.register('accommodation', AccommodationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
