from django.urls import path
from user import views

app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('me/', views.me, name='me'),
    path('login/', views.login),
    path('logout/', views.logout),
    path('refresh-token/', views.refresh_token),
]
