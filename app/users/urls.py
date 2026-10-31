from django.urls import path, include
from users import (
    views,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', views.UsersView, basename='user_api')
urlpatterns = [
    path('', include(router.urls)),
]
