from django.urls import path, include
from reports import (
    views,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', views.ReportsView, basename='reports_api')
urlpatterns = [
    path('', include(router.urls)),
]
