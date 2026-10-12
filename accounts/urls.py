from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("login/", views.SignInView.as_view(), name="login"),
    path("logout/", views.SignOutView.as_view(), name="logout"),
    path("security/", views.SecurityView.as_view(), name="security"),
    path(
        "security/password/",
        views.ChangePasswordView.as_view(),
        name="password_change",
    ),
    path(
        "password-reset/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        views.PasswordResetSentView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.PasswordResetSetView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.PasswordResetFinishedView.as_view(),
        name="password_reset_complete",
    ),
    path("addresses/", views.AddressListView.as_view(), name="addresses"),
    path("addresses/new/", views.AddressCreateView.as_view(), name="address_create"),
    path(
        "addresses/<int:pk>/edit/",
        views.AddressUpdateView.as_view(),
        name="address_update",
    ),
    path(
        "addresses/<int:pk>/delete/",
        views.AddressDeleteView.as_view(),
        name="address_delete",
    ),
    path(
        "addresses/<int:pk>/default-shipping/",
        views.MakeDefaultAddressView.as_view(kind="shipping"),
        name="address_default_shipping",
    ),
    path(
        "addresses/<int:pk>/default-billing/",
        views.MakeDefaultAddressView.as_view(kind="billing"),
        name="address_default_billing",
    ),
]
