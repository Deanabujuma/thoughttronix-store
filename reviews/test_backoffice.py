import re
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from .models import Review

MODERATION_FIELDS = ("status", "hidden_by_id", "hidden_at", "hidden_reason")


def snapshot(review):
    review.refresh_from_db()
    return {field: getattr(review, field) for field in MODERATION_FIELDS}


@pytest.fixture
def published_review(customer, product, delivered_order):
    return Review.objects.create(
        user=customer, product=product, rating=4, comment="Moderate me"
    )


@pytest.fixture
def hidden_review(published_review, staff_user):
    published_review.status = Review.Status.HIDDEN
    published_review.hidden_by = staff_user
    published_review.hidden_at = timezone.now()
    published_review.hidden_reason = "Off-topic"
    published_review.save()
    return published_review


def url_for(name, review):
    if name == "manage_reviews":
        return reverse("reviews:manage_reviews")
    return reverse(f"reviews:{name}", kwargs={"pk": review.pk})


# (who, URL name, method, the review it acts on, expected response).
# Restore acts on a hidden review; everything else on a published one.
PAGES = [
    ("manage_reviews", "get", "published_review"),
    ("manage_review_detail", "get", "published_review"),
]
ACTIONS = [
    ("manage_review_hide", "post", "published_review"),
    ("manage_review_restore", "post", "hidden_review"),
]
CASES = [
    *[("anonymous", *e, "login") for e in PAGES + ACTIONS],
    *[("customer", *e, HTTPStatus.FORBIDDEN) for e in PAGES + ACTIONS],
    *[("author", *e, HTTPStatus.FORBIDDEN) for e in PAGES + ACTIONS],
    *[("staff", n, "get", w, HTTPStatus.METHOD_NOT_ALLOWED) for n, _, w in ACTIONS],
    *[("staff without CSRF", *e, HTTPStatus.FORBIDDEN) for e in ACTIONS],
]


@pytest.mark.parametrize(
    ("who", "name", "method", "which", "expected"),
    CASES,
    ids=[f"{c[0]}-{c[1].removeprefix('manage_')}-{c[2]}" for c in CASES],
)
def test_moderation_is_staff_only_post_only_and_csrf_protected(
    request, other_customer, staff_user, who, name, method, which, expected
):
    """Anonymous visitors are sent to login; signed-in customers — the
    review's own author included — get 403. Staff can't hide or restore by
    GET (405) or without a CSRF token (403). No refused request ever
    changes the review."""
    review = request.getfixturevalue(which)
    url = url_for(name, review)
    before = snapshot(review)
    client = Client(enforce_csrf_checks=(who == "staff without CSRF"))
    signed_in = {
        "customer": other_customer,
        "author": review.user,
        "staff": staff_user,
        "staff without CSRF": staff_user,
    }
    if who in signed_in:
        client.force_login(signed_in[who])

    # Only POSTs carry a body; on a GET it would become the query string.
    data = {"reason": "Spam"} if method == "post" else {}
    response = getattr(client, method)(url, data)

    if expected == "login":
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == f"{reverse('accounts:login')}?next={url}"
    else:
        assert response.status_code == expected
    assert snapshot(review) == before


# --- Hiding ---------------------------------------------------------------------

REASON_REQUIRED = "Give a reason for hiding this review."
REASON_TOO_LONG = "Keep the reason to 200 characters or fewer."
HIDDEN = "Review hidden. It no longer appears in the store."
ALREADY_HIDDEN = "This review is already hidden; nothing was changed."


@pytest.mark.parametrize(
    ("start", "reason", "outcome", "stored", "message"),
    [
        pytest.param(
            "published",
            "  Off-topic rant \n",
            "hidden",
            "Off-topic rant",
            HIDDEN,
            id="trimmed reason",
        ),
        pytest.param("published", "x", "hidden", "x", HIDDEN, id="1 character"),
        pytest.param("published", "x" * 200, "hidden", "x" * 200, HIDDEN, id="200"),
        pytest.param("published", "", "refused", None, REASON_REQUIRED, id="blank"),
        pytest.param(
            "published", " \n\t ", "refused", None, REASON_REQUIRED, id="whitespace"
        ),
        pytest.param(
            "published", "x" * 201, "refused", None, REASON_TOO_LONG, id="201"
        ),
        pytest.param(
            "hidden",
            "A newer reason",
            "unchanged",
            None,
            ALREADY_HIDDEN,
            id="already hidden",
        ),
    ],
)
def test_hiding_needs_a_reason_and_keeps_an_accurate_record(
    client, staff_user, published_review, start, reason, outcome, stored, message
):
    review = published_review
    if start == "hidden":
        # Hidden earlier by another moderator, for another reason.
        original = get_user_model().objects.create_user(
            username="moderator", is_staff=True
        )
        review.status = Review.Status.HIDDEN
        review.hidden_by = original
        review.hidden_at = timezone.now() - timedelta(days=2)
        review.hidden_reason = "The original reason"
        review.save()
    before = snapshot(review)
    detail = reverse("reviews:manage_review_detail", kwargs={"pk": review.pk})
    client.force_login(staff_user)
    started = timezone.now()

    response = client.post(
        reverse("reviews:manage_review_hide", kwargs={"pk": review.pk}),
        {"reason": reason},
    )

    if outcome == "refused":
        # The detail page again, with the error beside the Hide form.
        assert response.status_code == HTTPStatus.OK
        assert message in response.content.decode()
        assert snapshot(review) == before
        return
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == detail
    assert [str(m) for m in get_messages(response.wsgi_request)] == [message]
    if outcome == "unchanged":
        assert snapshot(review) == before
        return
    review.refresh_from_db()
    assert review.status == Review.Status.HIDDEN
    assert review.hidden_by == staff_user
    assert review.hidden_at >= started
    assert review.hidden_reason == stored


# --- What a hidden review looks like afterwards ---------------------------------


@pytest.mark.parametrize("viewer", ["anonymous", "another customer", "author"])
def test_a_hidden_review_leaves_public_view_but_its_author_still_sees_why(
    client, customer, other_customer, staff_user, product, delivered_order, viewer
):
    author_review = Review.objects.create(
        user=customer, product=product, rating=1, comment="Words staff hid"
    )
    reviewer = get_user_model().objects.create_user(username="ana")
    Review.objects.create(
        user=reviewer, product=product, rating=5, comment="Words still public"
    )
    # Hidden through the real staff action, with a reason that holds HTML.
    moderator = Client()
    moderator.force_login(staff_user)
    moderator.post(
        reverse("reviews:manage_review_hide", kwargs={"pk": author_review.pk}),
        {"reason": "<b>Spam</b> & links"},
    )
    author_review.refresh_from_db()
    assert author_review.status == Review.Status.HIDDEN
    if viewer != "anonymous":
        client.force_login(customer if viewer == "author" else other_customer)
    edit = reverse("reviews:edit", kwargs={"slug": product.slug})
    delete = reverse("reviews:delete", kwargs={"slug": product.slug})
    only_the_public_one = 'aria-label="Rated 5.0 out of 5, 1 review"'

    page = client.get(product.get_absolute_url()).content.decode()
    cards = [
        client.get(reverse("products:catalog")).content.decode(),
        client.get(
            reverse("products:category", kwargs={"slug": product.category.slug})
        ).content.decode(),
    ]

    # Nobody's summary — the author's included — counts the hidden review.
    assert only_the_public_one in page
    for card_page in cards:
        assert only_the_public_one in card_page
    assert "Words still public" in page
    assert "<b>Spam</b>" not in page  # never rendered as HTML, for anyone
    if viewer == "author":
        assert page.count("Words staff hid") == 1  # pinned, not in the list
        assert page.index("Your review") < page.index("Words staff hid")
        assert "Hidden by staff: &lt;b&gt;Spam&lt;/b&gt; &amp; links" in page
        assert f'href="{delete}"' in page
        assert f'href="{edit}"' not in page
    else:
        assert "Words staff hid" not in page
        assert "Spam" not in page
        assert "Hidden by staff" not in page


# --- The list -------------------------------------------------------------------

LIST = reverse("reviews:manage_reviews")


def detail_url(review):
    return reverse("reviews:manage_review_detail", kwargs={"pk": review.pk})


def make_reviews(product, count, *, hidden_by=None, start=0):
    """``count`` reviews by fresh customers, a day apart, newest first."""
    now = timezone.now()
    made = []
    for n in range(start, start + count):
        user = get_user_model().objects.create_user(username=f"shopper{n:02}")
        fields = {}
        if hidden_by:
            fields = {
                "status": Review.Status.HIDDEN,
                "hidden_by": hidden_by,
                "hidden_at": now,
                "hidden_reason": "Off-topic",
            }
        made.append(
            Review.objects.create(
                user=user,
                product=product,
                rating=3,
                comment=f"Comment {n:02}",
                created_at=now - timedelta(days=n),
                **fields,
            )
        )
    return made


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client


def test_the_list_shows_25_a_page_newest_first(staff_client, product):
    make_reviews(product, 26)

    first = staff_client.get(LIST)
    second = staff_client.get(LIST, {"page": 2})

    comments = [r.comment for r in first.context["reviews"]]
    assert comments == [f"Comment {n:02}" for n in range(25)]
    assert [r.comment for r in second.context["reviews"]] == ["Comment 25"]
    assert "26 reviews" in first.content.decode()


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("PUBLISHED", ["Comment 00", "Comment 01"]),
        ("HIDDEN", ["Comment 02"]),
        ("", ["Comment 00", "Comment 01", "Comment 02"]),
        ("hidden", ["Comment 00", "Comment 01", "Comment 02"]),  # not a value
        ("BOGUS", ["Comment 00", "Comment 01", "Comment 02"]),
    ],
)
def test_the_list_filters_by_status_and_ignores_unknown_values(
    staff_client, staff_user, product, status, expected
):
    make_reviews(product, 2)
    make_reviews(product, 1, hidden_by=staff_user, start=2)

    response = staff_client.get(LIST, {"status": status})

    assert [r.comment for r in response.context["reviews"]] == expected


def test_the_filter_is_kept_across_pages(staff_client, staff_user, product):
    make_reviews(product, 26, hidden_by=staff_user)

    page = staff_client.get(LIST, {"status": "HIDDEN"}).content.decode()

    assert 'href="?status=HIDDEN&amp;page=2"' in page


def test_a_bad_page_number_on_the_list_is_404(staff_client, product):
    make_reviews(product, 1)

    assert staff_client.get(LIST, {"page": 99}).status_code == HTTPStatus.NOT_FOUND


def test_the_list_shows_each_reviews_columns(staff_client, staff_user, product):
    long_comment = "A" * 100
    user = get_user_model().objects.create_user(username="zx_listed")
    review = Review.objects.create(
        user=user, product=product, rating=4, comment=long_comment
    )
    review.hide(staff_user, "Off-topic")

    page = staff_client.get(LIST).content.decode()

    assert f'href="{product.get_absolute_url()}"' in page
    assert product.name in page
    assert "zx_listed" in page
    assert "★★★★☆" in page and "Rated 4 out of 5" in page
    assert "A" * 79 + "…" in page and long_comment not in page
    assert review.created_at.strftime("%b") in page
    assert "Hidden by employee" in page
    assert f'href="{detail_url(review)}"' in page


def test_a_deleted_moderator_shows_as_former_staff_member(staff_client, product):
    gone = get_user_model().objects.create_user(username="gone", is_staff=True)
    (review,) = make_reviews(product, 1, hidden_by=gone)
    gone.delete()

    review.refresh_from_db()
    assert review.status == Review.Status.HIDDEN  # still hidden
    assert review.hidden_by is None
    for url in [LIST, detail_url(review)]:
        assert "Former staff member" in staff_client.get(url).content.decode()


def test_the_list_has_designed_empty_states(staff_client, product):
    assert "No reviews yet" in staff_client.get(LIST).content.decode()

    make_reviews(product, 1)
    filtered = staff_client.get(LIST, {"status": "HIDDEN"}).content.decode()

    assert "No reviews with that status" in filtered
    assert "Show all reviews" in filtered


def test_the_reviews_tab_sits_between_discount_codes_and_dashboard(staff_client):
    page = staff_client.get(LIST).content.decode()

    tabs = page[page.index('role="tablist"') :]
    assert tabs.index(">Discount codes<") < tabs.index(">Reviews<")
    assert tabs.index(">Reviews<") < tabs.index(">Dashboard<")
    assert re.search(r'class="tab tab-active"\s+href="' + re.escape(LIST), page)


# --- The detail page ------------------------------------------------------------


def test_the_detail_page_shows_the_whole_review(staff_client, published_review):
    published_review.comment = 'Line one <script>alert("x")</script>\nLine two'
    published_review.edited_at = timezone.now()
    published_review.save()

    page = staff_client.get(detail_url(published_review)).content.decode()

    assert published_review.product.name in page
    assert published_review.user.username in page
    assert "Posted" in page and "Edited" in page
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;<br>Line two" in page
    assert '<script>alert("x")' not in page
    assert "Hide review" in page
    assert "Restore review" not in page


def test_a_hidden_reviews_detail_shows_its_record_and_restore(
    staff_client, hidden_review
):
    page = staff_client.get(detail_url(hidden_review)).content.decode()

    assert "Hidden by" in page and "employee" in page
    assert "Off-topic" in page
    assert "Restore review" in page
    assert "Hide review" not in page


def test_there_is_no_delete_action_in_the_back_office(staff_client, published_review):
    pages = [
        staff_client.get(LIST).content.decode(),
        staff_client.get(detail_url(published_review)).content.decode(),
    ]

    for page in pages:
        backoffice = page[page.index('role="tablist"') :]
        assert "Delete" not in backoffice
        assert "/delete/" not in backoffice


# --- Restoring ------------------------------------------------------------------

RESTORED = "Review restored. It appears in the store again."
ALREADY_PUBLISHED = "This review is already published; nothing was changed."


def restore(client, review):
    return client.post(
        reverse("reviews:manage_review_restore", kwargs={"pk": review.pk})
    )


def test_restoring_publishes_and_clears_the_record(staff_client, hidden_review):
    response = restore(staff_client, hidden_review)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == detail_url(hidden_review)
    assert [str(m) for m in get_messages(response.wsgi_request)] == [RESTORED]
    hidden_review.refresh_from_db()
    assert hidden_review.status == Review.Status.PUBLISHED
    assert hidden_review.hidden_by is None
    assert hidden_review.hidden_at is None
    assert hidden_review.hidden_reason == ""


def test_restoring_twice_changes_nothing(staff_client, published_review):
    before = snapshot(published_review)

    response = restore(staff_client, published_review)

    assert response.url == detail_url(published_review)
    assert [str(m) for m in get_messages(response.wsgi_request)] == [ALREADY_PUBLISHED]
    assert snapshot(published_review) == before


def test_a_restored_review_is_public_and_counted_again(
    client, staff_user, hidden_review
):
    product = hidden_review.product
    moderator = Client()
    moderator.force_login(staff_user)

    assert "Moderate me" not in client.get(product.get_absolute_url()).content.decode()
    restore(moderator, hidden_review)

    page = client.get(product.get_absolute_url()).content.decode()
    cards = client.get(reverse("products:catalog")).content.decode()
    assert "Moderate me" in page
    assert 'aria-label="Rated 4.0 out of 5, 1 review"' in page
    assert 'aria-label="Rated 4.0 out of 5, 1 review"' in cards


def test_hide_restore_hide_records_the_new_moderation(staff_user, published_review):
    published_review.hide(staff_user, "First reason")
    published_review.restore()

    assert published_review.hide(staff_user, "Second reason") is True
    assert published_review.hidden_reason == "Second reason"


# --- Who may moderate -------------------------------------------------------------


def test_a_superuser_without_staff_status_is_refused(client, published_review):
    boss = get_user_model().objects.create_user(username="boss", is_superuser=True)
    client.force_login(boss)

    assert client.get(LIST).status_code == HTTPStatus.FORBIDDEN
    assert restore(client, published_review).status_code == HTTPStatus.FORBIDDEN


def test_a_staff_member_may_moderate_a_review_they_wrote_as_a_customer(
    client, published_review
):
    author = published_review.user
    author.is_staff = True
    author.save()
    client.force_login(author)

    client.post(
        reverse("reviews:manage_review_hide", kwargs={"pk": published_review.pk}),
        {"reason": "Written before I joined"},
    )

    published_review.refresh_from_db()
    assert published_review.status == Review.Status.HIDDEN
