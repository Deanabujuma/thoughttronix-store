from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from orders.models import Order

from .models import Review
from .templatetags.review_extras import star_glyphs


def reviewer(name):
    return get_user_model().objects.create_user(username=name)


def test_the_summary_averages_and_counts_only_published_reviews(
    client, product, staff_user
):
    for name, rating in [("ana", 5), ("ben", 4), ("cy", 4)]:
        Review.objects.create(user=reviewer(name), product=product, rating=rating)
    # Counted, it would drag the summary to 3.5 from 4 reviews.
    Review.objects.create(
        user=reviewer("dee"),
        product=product,
        rating=1,
        status=Review.Status.HIDDEN,
        hidden_by=staff_user,
        hidden_at=timezone.now(),
        hidden_reason="Off-topic",
    )

    response = client.get(product.get_absolute_url())

    # (5 + 4 + 4) / 3 = 4.333…, shown to one decimal place.
    assert 'aria-label="Rated 4.3 out of 5, 3 reviews"' in response.content.decode()


def page_for(client, product):
    return client.get(product.get_absolute_url()).content.decode()


def hide(review, by):
    review.status = Review.Status.HIDDEN
    review.hidden_by, review.hidden_at = by, timezone.now()
    review.hidden_reason = "Off-topic"
    review.save()


# --- The summary --------------------------------------------------------------


def test_a_product_without_reviews_says_so_in_words(client, product):
    page = page_for(client, product)

    assert "No reviews yet" in page
    assert "No reviews yet. Customers who've received this product can share" in page
    assert "0.0" not in page
    assert "Rated" not in page


def test_one_review_is_singular(client, product):
    Review.objects.create(user=reviewer("ana"), product=product, rating=5)

    assert 'aria-label="Rated 5.0 out of 5, 1 review"' in page_for(client, product)


def test_the_summary_stars_are_hidden_from_screen_readers(client, product):
    Review.objects.create(user=reviewer("ana"), product=product, rating=4)
    Review.objects.create(user=reviewer("ben"), product=product, rating=5)

    assert '<span class="text-warning" aria-hidden="true">★★★★½</span>' in page_for(
        client, product
    )


@pytest.mark.parametrize(
    ("value", "glyphs"),
    [
        (None, ""),
        (1, "★☆☆☆☆"),
        (3, "★★★☆☆"),
        (4.2, "★★★★☆"),
        (4.25, "★★★★½"),
        (4.3, "★★★★½"),
        (4.74, "★★★★½"),
        (4.75, "★★★★★"),
        (5, "★★★★★"),
    ],
)
def test_stars_round_to_the_nearest_half(value, glyphs):
    assert star_glyphs(value) == glyphs


# --- The public list ----------------------------------------------------------


def test_a_review_is_signed_verified_buyer_and_never_by_account(client, product):
    user = get_user_model().objects.create_user(
        username="zx_reviewer",
        email="zx.private@example.com",
        first_name="Quillon",
        last_name="Marchbanks",
    )
    Review.objects.create(user=user, product=product, rating=4, comment="Solid hub.")

    page = page_for(client, product)

    assert "Solid hub." in page
    assert "Verified buyer" in page
    assert "Rated 4 out of 5" in page
    assert "Posted" in page
    for identity in ["zx_reviewer", "zx.private", "Quillon", "Marchbanks"]:
        assert identity not in page


def test_a_comment_is_escaped_with_line_breaks_kept(client, product):
    Review.objects.create(
        user=reviewer("ana"),
        product=product,
        rating=1,
        comment='<script>alert("x")</script>\nSecond line',
    )

    page = page_for(client, product)

    assert '<script>alert("x")</script>' not in page
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;<br>Second line" in page


def test_hidden_reviews_never_appear_publicly(client, product, staff_user):
    review = Review.objects.create(
        user=reviewer("ana"), product=product, rating=1, comment="Hidden words"
    )
    hide(review, staff_user)

    page = page_for(client, product)

    assert "Hidden words" not in page
    assert "No reviews yet" in page


def test_the_list_is_newest_first(client, product):
    now = timezone.now()
    for name, days_ago in [("ana", 3), ("ben", 1), ("cy", 2)]:
        Review.objects.create(
            user=reviewer(name),
            product=product,
            rating=4,
            comment=f"By {name}",
            created_at=now - timedelta(days=days_ago),
        )

    page = page_for(client, product)

    assert page.index("By ben") < page.index("By cy") < page.index("By ana")


# --- The "Your review" area ---------------------------------------------------


def test_anonymous_visitors_are_invited_to_sign_in(client, product):
    page = page_for(client, product)

    login = reverse("accounts:login")
    assert f'href="{login}?next={product.get_absolute_url()}"' in page
    assert "Sign in to review" in page
    assert "Write a review" not in page


@pytest.mark.parametrize(
    "status", [None, Order.Status.PLACED, Order.Status.SHIPPED, Order.Status.CANCELLED]
)
def test_a_customer_who_hasnt_received_it_is_told_why(
    client, customer, product, order_for, status
):
    if status:
        order_for(customer, status, product)
    client.force_login(customer)

    page = page_for(client, product)

    assert "Only customers who've received this product can review it." in page
    assert "Write a review" not in page


def test_an_eligible_customer_is_offered_the_form(
    client, customer, product, delivered_order
):
    client.force_login(customer)

    page = page_for(client, product)

    create = reverse("reviews:create", kwargs={"slug": product.slug})
    assert f'href="{create}"' in page
    assert "Write a review" in page
    assert "Only customers who've received" not in page


def test_the_authors_review_is_pinned_once(client, customer, product, delivered_order):
    Review.objects.create(
        user=customer, product=product, rating=4, comment="My own words"
    )
    Review.objects.create(
        user=reviewer("ana"), product=product, rating=2, comment="Someone else"
    )
    client.force_login(customer)

    page = page_for(client, product)

    assert "Your review" in page
    assert page.count("My own words") == 1
    assert page.index("Your review") < page.index("My own words")
    assert page.index("My own words") < page.index("Someone else")
    assert "Write a review" not in page


def test_an_author_sees_their_review_as_the_only_one_without_an_empty_state(
    client, customer, product, delivered_order
):
    Review.objects.create(user=customer, product=product, rating=4, comment="Mine")
    client.force_login(customer)

    page = page_for(client, product)

    assert "Your review" in page
    assert "No reviews yet" not in page


@pytest.mark.parametrize("role", ["is_staff", "is_superuser"])
def test_staff_and_the_admin_are_shown_no_review_controls(
    client, customer, product, delivered_order, role
):
    setattr(customer, role, True)
    customer.save()
    client.force_login(customer)

    page = page_for(client, product)

    assert "Write a review" not in page
    assert "Sign in to review" not in page
    assert "Only customers who've received" not in page
    assert "Your review" not in page


# --- The author's controls (Phase 2) ------------------------------------------


def controls(product):
    return (
        f'href="{reverse("reviews:edit", kwargs={"slug": product.slug})}"',
        f'href="{reverse("reviews:delete", kwargs={"slug": product.slug})}"',
    )


def test_an_eligible_author_is_offered_edit_and_delete(
    client, customer, product, delivered_order
):
    Review.objects.create(user=customer, product=product, rating=4)
    client.force_login(customer)
    edit, delete = controls(product)

    page = page_for(client, product)

    assert edit in page
    assert delete in page


@pytest.mark.parametrize("change", ["promoted", "order cancelled", "hidden"])
def test_an_author_who_may_not_edit_is_offered_delete_only(
    client, customer, staff_user, product, delivered_order, change
):
    review = Review.objects.create(user=customer, product=product, rating=4)
    if change == "promoted":
        customer.is_staff = True
        customer.save()
    elif change == "order cancelled":
        delivered_order.status = Order.Status.CANCELLED
        delivered_order.save()
    else:
        hide(review, staff_user)
    client.force_login(customer)
    edit, delete = controls(product)

    page = page_for(client, product)

    assert "Your review" in page
    assert edit not in page
    assert delete in page


def test_other_visitors_see_no_edit_or_delete_controls(client, other_customer, product):
    Review.objects.create(user=reviewer("ana"), product=product, rating=4)
    edit, delete = controls(product)

    for visit in ["anonymous", "another customer"]:
        if visit == "another customer":
            client.force_login(other_customer)
        page = page_for(client, product)
        assert edit not in page
        assert delete not in page


# --- "Edited <date>" ----------------------------------------------------------


def test_an_edited_review_shows_both_dates(client, customer, product):
    posted = timezone.now().replace(year=2026, month=3, day=4)
    edited = timezone.now().replace(year=2026, month=5, day=6)
    Review.objects.create(
        user=customer,
        product=product,
        rating=4,
        comment="Edited words",
        created_at=posted,
        edited_at=edited,
    )

    page = page_for(client, product)

    assert "Posted" in page and "Mar 4, 2026" in page
    assert "Edited" in page and "May 6, 2026" in page


def test_an_unedited_review_shows_no_edited_label(client, product):
    Review.objects.create(user=reviewer("ana"), product=product, rating=4)

    assert "Edited" not in page_for(client, product)


def test_the_pinned_review_shows_its_edited_date_too(
    client, customer, product, delivered_order
):
    Review.objects.create(
        user=customer,
        product=product,
        rating=4,
        edited_at=timezone.now().replace(year=2026, month=5, day=6),
    )
    client.force_login(customer)

    page = page_for(client, product)

    assert page.index("Your review") < page.index("May 6, 2026")


def test_an_order_status_change_leaves_the_review_public(
    client, customer, product, delivered_order
):
    Review.objects.create(
        user=customer, product=product, rating=5, comment="Still counts"
    )
    delivered_order.status = Order.Status.CANCELLED
    delivered_order.save()

    page = page_for(client, product)

    assert "Still counts" in page
    assert 'aria-label="Rated 5.0 out of 5, 1 review"' in page
