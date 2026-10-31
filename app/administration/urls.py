from django.urls import path, include
from administration import (
    views,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', views.AdministrationsView, basename='administration_api')
urlpatterns = [
    path('', include(router.urls)),
]
