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
    # Back office — staff-only, pk URLs per the URL conventions.
    path(
        "backoffice/reviews/",
        views.ManageReviewListView.as_view(),
        name="manage_reviews",
    ),
    path(
        "backoffice/reviews/restrictions/",
        views.ManageRestrictionListView.as_view(),
        name="manage_restrictions",
    ),
    path(
        "backoffice/reviews/restrictions/<int:pk>/clear/",
        views.ClearRestrictionView.as_view(),
        name="manage_restriction_clear",
    ),
    path(
        "backoffice/reviews/<int:pk>/",
        views.ManageReviewDetailView.as_view(),
        name="manage_review_detail",
    ),
    path(
        "backoffice/reviews/<int:pk>/hide/",
        views.HideReviewView.as_view(),
        name="manage_review_hide",
    ),
    path(
        "backoffice/reviews/<int:pk>/restore/",
        views.RestoreReviewView.as_view(),
        name="manage_review_restore",
    ),
]
