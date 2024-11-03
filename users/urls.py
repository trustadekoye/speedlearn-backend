from django.urls import path
from .views import (
    UserRegisterView,
    UserLoginView,
    UserView,
    MDAView,
    PasswordResetView,
    PasswordResetConfirmView,
)

urlpatterns = [
    path("register", UserRegisterView.as_view(), name="register"),
    path("login", UserLoginView.as_view(), name="login"),
    path("user", UserView.as_view(), name="user"),
    path("mda", MDAView.as_view(), name="mda"),
    path("password-reset", PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/confirm",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
