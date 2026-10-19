from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone

from .models import Review, ReviewRestriction


def test_the_moderation_fields_are_read_only(admin_client, customer, product):
    review = Review.objects.create(user=customer, product=product, rating=4)

    page = admin_client.get(
        reverse("admin:reviews_review_change", args=[review.pk])
    ).content.decode()

    assert 'name="rating"' in page
    assert 'name="comment"' in page
    for field in ["status", "hidden_by", "hidden_at", "hidden_reason"]:
        assert f'name="{field}"' not in page


def test_the_list_searches_and_filters(admin_client, customer, product):
    Review.objects.create(user=customer, product=product, rating=4)
    changelist = reverse("admin:reviews_review_changelist")

    by_user = admin_client.get(changelist, {"q": "customer"})
    by_product = admin_client.get(changelist, {"q": "Seraphine"})
    by_status = admin_client.get(changelist, {"status__exact": "HIDDEN"})

    assert by_user.status_code == by_product.status_code == HTTPStatus.OK
    assert by_user.context["cl"].result_count == 1
    assert by_product.context["cl"].result_count == 1
    assert by_status.context["cl"].result_count == 0


# --- Restrictions in the admin ----------------------------------------------------


def hidden_review(customer, product, staff_user):
    return Review.objects.create(
        user=customer,
        product=product,
        rating=1,
        status=Review.Status.HIDDEN,
        hidden_by=staff_user,
        hidden_at=timezone.now(),
        hidden_reason="Off-topic",
    )


def test_deleting_a_hidden_review_in_the_admin_creates_no_restriction(
    admin_client, customer, staff_user, product
):
    review = hidden_review(customer, product, staff_user)

    response = admin_client.post(
        reverse("admin:reviews_review_delete", args=[review.pk]), {"post": "yes"}
    )

    assert response.status_code == HTTPStatus.FOUND
    assert not Review.objects.exists()
    assert not ReviewRestriction.objects.exists()


def test_restrictions_cannot_be_added_or_edited_in_the_admin(
    admin_client, customer, staff_user, product
):
    restriction = ReviewRestriction.objects.create(
        user=customer,
        product=product,
        hidden_reason="Off-topic",
        hidden_by=staff_user,
        hidden_at=timezone.now(),
    )

    add = admin_client.get(reverse("admin:reviews_reviewrestriction_add"))
    change = admin_client.get(
        reverse("admin:reviews_reviewrestriction_change", args=[restriction.pk])
    ).content.decode()

    assert add.status_code == HTTPStatus.FORBIDDEN
    for field in ["user", "product", "hidden_reason", "hidden_by", "hidden_at"]:
        assert f'name="{field}"' not in change


def test_the_admin_can_delete_a_restriction_and_search_them(
    admin_client, customer, staff_user, product
):
    restriction = ReviewRestriction.objects.create(
        user=customer,
        product=product,
        hidden_reason="Off-topic",
        hidden_by=staff_user,
        hidden_at=timezone.now(),
    )
    changelist = reverse("admin:reviews_reviewrestriction_changelist")

    assert (
        admin_client.get(changelist, {"q": "customer"}).context["cl"].result_count == 1
    )
    assert (
        admin_client.get(changelist, {"q": "Seraphine"}).context["cl"].result_count == 1
    )
    admin_client.post(
        reverse("admin:reviews_reviewrestriction_delete", args=[restriction.pk]),
        {"post": "yes"},
    )
    assert not ReviewRestriction.objects.exists()
