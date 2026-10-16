import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError

from .models import Wishlist, WishlistItem


def test_wishlist_str(wishlist):
    assert str(wishlist) == "Wishlist for customer"


def test_wishlist_item_str(saved_item):
    assert str(saved_item) == "Seraphine Home Hub"


def test_for_user_creates_the_wishlist_once(customer):
    first = Wishlist.for_user(customer)
    second = Wishlist.for_user(customer)

    assert first == second
    assert Wishlist.objects.count() == 1


def test_wishlist_product_pair_is_unique(saved_item):
    with pytest.raises(IntegrityError):
        WishlistItem.objects.create(
            wishlist=saved_item.wishlist, product=saved_item.product
        )


def test_saving_twice_keeps_one_item(wishlist, product):
    first = wishlist.save_product(product)
    second = wishlist.save_product(product)

    assert first == second
    assert wishlist.items.count() == 1


def test_removing_a_saved_product(customer, saved_item, product):
    Wishlist.remove_for(customer, product)

    assert not WishlistItem.objects.exists()


def test_removing_an_unsaved_product_is_harmless(customer, wishlist, product):
    Wishlist.remove_for(customer, product)

    assert wishlist.items.count() == 0


def test_removing_never_creates_a_wishlist(customer, product):
    Wishlist.remove_for(customer, product)

    assert not Wishlist.objects.exists()


def test_has_saved_is_false_without_a_wishlist_and_creates_none(customer, product):
    assert not Wishlist.has_saved(customer, product)
    assert not Wishlist.objects.exists()


def test_has_saved_is_true_only_for_the_saver(customer, other_customer, saved_item):
    assert Wishlist.has_saved(customer, saved_item.product)
    assert not Wishlist.has_saved(other_customer, saved_item.product)


def test_has_saved_is_false_for_anonymous_users(saved_item):
    assert not Wishlist.has_saved(AnonymousUser(), saved_item.product)


def test_deleting_a_product_removes_it_from_wishlists(wishlist, saved_item, product):
    product.delete()

    assert not WishlistItem.objects.exists()
    assert Wishlist.objects.filter(pk=wishlist.pk).exists()


def test_deleting_a_user_removes_their_wishlist(customer, saved_item):
    customer.delete()

    assert not Wishlist.objects.exists()
    assert not WishlistItem.objects.exists()


def test_an_unavailable_product_stays_saved(customer, saved_item, product):
    product.is_available = False
    product.save()

    assert Wishlist.has_saved(customer, product)


def test_items_are_newest_first(wishlist, product, unavailable_product):
    older = wishlist.save_product(product)
    newer = wishlist.save_product(unavailable_product)

    assert list(wishlist.items.all()) == [newer, older]
