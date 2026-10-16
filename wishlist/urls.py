from django.urls import path

from . import views

app_name = "wishlist"

urlpatterns = [
    path("", views.WishlistView.as_view(), name="list"),
    path("save/<int:pk>/", views.SaveToWishlistView.as_view(), name="save"),
    path("remove/<int:pk>/", views.RemoveFromWishlistView.as_view(), name="remove"),
]
