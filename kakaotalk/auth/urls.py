# myproject/auth/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('kakao/login/', views.kakao_login_request, name='kakao_login'),
    path('kakao/callback/', views.kakao_login_callback, name='kakao_callback'),
    path('kakao/logout/', views.kakao_logout_request, name='kakao_logout'),
]