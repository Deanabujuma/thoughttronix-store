from http import HTTPStatus

from django.urls import reverse

from .models import Review


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
