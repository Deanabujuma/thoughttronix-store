from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path(
        "products/<slug:slug>/review/",
        views.ReviewCreateView.as_view(),
        name="create",
    ),
    path(
        "products/<slug:slug>/review/edit/",
        views.ReviewUpdateView.as_view(),
        name="edit",
    ),
    path(
        "products/<slug:slug>/review/delete/",
        views.ReviewDeleteView.as_view(),
        name="delete",
    ),
]
