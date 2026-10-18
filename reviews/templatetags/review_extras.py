from decimal import ROUND_HALF_UP, Decimal

from django import template

register = template.Library()


@register.filter
def star_glyphs(value):
    """Five star glyphs for a rating, rounded to the nearest half.

    ``4.3`` → ``★★★★½``, ``3`` → ``★★★☆☆``. ``None`` (no reviews) → ``""``.
    The glyphs are decoration: callers mark them ``aria-hidden`` and give
    the number in words.
    """
    if value is None:
        return ""
    halves = int((Decimal(str(value)) * 2).quantize(Decimal(1), ROUND_HALF_UP))
    full, half = divmod(halves, 2)
    return "★" * full + "½" * half + "☆" * (5 - full - half)
