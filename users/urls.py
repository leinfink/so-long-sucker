from django.urls import re_path
from .views import CustomLoginView, CustomLogoutView, CustomSignupView

urlpatterns = [
    re_path(r"^login/$", CustomLoginView.as_view(), name='account_login'),
    re_path(r"^logout/$", CustomLogoutView.as_view(), name='account_logout'),
    re_path(r"^signup/$", CustomSignupView.as_view(), name='account_signup'),
]
