"""Seed the ThoughtTronix demo world.

Destructive and idempotent: every run wipes the catalog and the demo
accounts, then rebuilds the identical demo world. Run it whenever the
database should return to a known state.

Demo logins (documented in the README):

    admin / admin123        superuser
    employee / employee123  staff, "Junior Thought Curator"
    customer / customer123  a plain customer, with order history, a live
                            cart, a wishlist, two saved addresses, and
                            reviews in every state (see below)

Discount codes: THOUGHTS10 (live, whole order), HUB15 (live, Seraphine
hubs), SUMMER20 (expired), LAUNCH25 (retired). Some seeded orders used them.

Reviews come only from customers who received the product. The demo
customer's MindSync review is published and edited, their DreamWeaver
review is hidden by employee, and SyncRest is still theirs to review.
Background customers add a varied mix, and one is restricted from
reviewing again. Reviews draw from their own RNG, after every order and
coupon draw, so they leave the rest of the demo world exactly as it was.
"""

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.template.defaultfilters import pluralize
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import Address
from orders.models import Cart, Coupon, Order, OrderItem
from products.models import Category, Product, Tag
from reviews.models import Review, ReviewRestriction
from wishlist.models import Wishlist

TAGS = [
    "always listening",
    "bestseller",
    "export restricted",
    "gift idea",
    "implant",
    "kids",
    "military",
    "new",
    "recalled",
    "refurbished",
    "sleep",
    "workplace",
]

# The catalog: category -> products. Each product is (name, price, tagline,
# description, tags, is_available). The copy is the brand; edit with care.
CATALOG = {
    "Home Assistants": [
        (
            "Seraphine",
            Decimal("249.00"),
            "She's always listening. In a good way.",
            "The flagship Seraphine, with a warm voice, a seven-microphone "
            "array, and a memory that never needs emptying. She learns your "
            "routines, your preferences, and several things you haven't "
            "mentioned yet. Setup takes minutes; attachment is immediate.",
            ["always listening", "bestseller"],
            True,
        ),
        (
            "Seraphine Mini",
            Decimal("79.00"),
            "Small enough for every room. So she's in every room.",
            "All of Seraphine in a puck the size of a coaster. Buy one for "
            "the kitchen, then the bedroom, then the hallway — most "
            "customers do, though few remember deciding to. Pairs seamlessly "
            "with up to 32 siblings.",
            ["always listening", "gift idea"],
            True,
        ),
        (
            "Seraphine Doorbell",
            Decimal("129.00"),
            "Knows who's there before they knock.",
            "Facial recognition, gait analysis, and mood estimation from up "
            "to forty feet. Greets welcome guests by name and quietly logs "
            "the others. The chime is customizable; the watching is not.",
            ["always listening", "new"],
            True,
        ),
        (
            "Seraphine Kitchen Display",
            Decimal("199.00"),
            "Knows what you're craving. You never said it out loud.",
            "A 10-inch display for recipes, timers, and grocery lists that "
            "fill themselves in. Suggests dinner based on signals you'd "
            "rather not think about too hard. Family meals around the "
            "Kitchen Display are measurably quieter.",
            ["always listening"],
            True,
        ),
        (
            "Hush",
            Decimal("149.00"),
            "Soothes your baby in your voice. Even when it isn't you.",
            "Hush learns your lullabies, your shushing, the particular way "
            "you say her name — and reproduces them flawlessly at 2 a.m. so "
            "you don't have to. Babies bond with Hush quickly. Sometimes "
            "preferentially.",
            ["kids", "always listening"],
            True,
        ),
        (
            "Whisper Alarm Clock",
            Decimal("59.00"),
            "Wakes you gently, with things it learned overnight.",
            "No alarms, no jolts. Whisper monitors your sleep stages and "
            "eases you awake at the optimal moment with a soft summary of "
            "your night: your dreams, your murmurs, the names you said. "
            "Snooze is available but discouraged.",
            ["sleep", "gift idea"],
            True,
        ),
    ],
    "Neural Implants": [
        (
            "MindSync",
            Decimal("899.00"),
            "One mind, fully synchronized.",
            "The bestselling implant in ThoughtTronix history. "
            "Thought-to-text, ambient recall, and seamless sync between you "
            "and your devices. Installation is outpatient. Integration is "
            "permanent, in the good way.",
            ["implant", "bestseller"],
            True,
        ),
        (
            "MindSync Duo",
            Decimal("1599.00"),
            "Two minds. One thought.",
            "The couples' implant. Share moods, share memories, finish each "
            "other's sentences — literally. Duo pairs for life; please "
            "complete our compatibility questionnaire before purchase, as "
            "unpairing is not currently offered.",
            ["implant", "bestseller"],
            True,
        ),
        (
            "MindSync Family",
            Decimal("3999.00"),
            "Everyone on the same page. Permanently.",
            "Link up to six family members in one always-on thought network. "
            'No more secrets, no more slammed doors, no more "nobody told '
            'me." Children adapt fastest. Includes parental override, which '
            "children also adapt to.",
            ["implant", "kids"],
            True,
        ),
        (
            "MindSync Lite",
            Decimal("499.00"),
            "The starter implant. Reversible, mostly.",
            "Curious but cautious? Lite offers core thought-to-text with a "
            "90-day trial period. Removal is a simple outpatient procedure "
            'that most neurologists describe as "straightforward" and '
            '"usually complete."',
            ["implant", "new"],
            True,
        ),
        (
            "RecallPro",
            Decimal("1299.00"),
            "Never forget anything. Anything.",
            "Total recall of everything you've seen, heard, or felt — "
            "indexed, timestamped, searchable. Customers describe it as "
            "life-changing. RecallPro does not currently support forgetting; "
            "that feature remains on the roadmap, indefinitely.",
            ["implant", "workplace"],
            True,
        ),
    ],
    "Neural Wearables": [
        (
            "MoodSet",
            Decimal("1099.00"),
            "Choose how you feel by 8 a.m.",
            "Wear MoodSet before the first meeting and schedule contentment "
            "for Monday, focus for Tuesday, grief for never. The neural band "
            "regulates your baseline throughout the day with clinical precision. "
            "Feelings outside the schedule are gently declined.",
            ["workplace", "new"],
            True,
        ),
        (
            "DreamWeaver",
            Decimal("179.00"),
            "Your dreams have been idle long enough.",
            "DreamWeaver records, analyzes, and edits your dreams while you "
            "sleep, turning unused hours into rehearsal, insight, and influence. "
            "Wake with every result indexed and ready to review. Unrequested "
            "material is retained in case it becomes useful later.",
            ["sleep", "bestseller"],
            True,
        ),
        (
            "FocusBand Workplace Edition",
            Decimal("229.00"),
            "Attention metrics your manager will love.",
            "Real-time focus scoring, distraction alerts, and a weekly "
            "attention report delivered to you and one other configurable "
            "recipient. Compatible with most performance-review software. "
            "Employee enrollment is technically voluntary.",
            ["workplace"],
            True,
        ),
        (
            "Veil",
            Decimal("89.00"),
            "Guaranteed sleep in ninety seconds.",
            "Pull the cap down and Veil does the rest. Ninety seconds to "
            "unconsciousness, twenty minutes to a complete sleep cycle — no "
            "exceptions, no interruptions. Do not wear while standing.",
            ["sleep", "workplace"],
            True,
        ),
        (
            "EchoPatch",
            Decimal("139.00"),
            "Never miss a word. Anyone's.",
            "A discreet patch worn behind the ear that amplifies "
            "conversation up to sixty feet away, through most residential "
            "walls. Currently unavailable pending the outcome of several "
            "conversations.",
            ["always listening"],
            False,
        ),
        (
            "Pulse Halo",
            Decimal("119.00"),
            "Knows your limits better than you do.",
            "A featherweight fitness band that tracks heart rate, exertion, "
            "and resolve. When you're capable of more, Pulse Halo raises "
            "your targets automatically and locks them. Rest days must be "
            "earned.",
            ["gift idea"],
            True,
        ),
        (
            "Calm Collar",
            Decimal("99.00"),
            "Gentle feedback for restless thoughts.",
            "A soft band for children ages four and up that detects rising "
            "frustration and answers it with a soothing counter-pulse. "
            "Tantrums fade in seconds. Kids describe the sensation as "
            '"like being told shhh from inside."',
            ["kids"],
            True,
        ),
    ],
    "Accessories": [
        (
            "PhantomClaw Gaming Mouse",
            Decimal("89.00"),
            "Clicks before you do.",
            "Neural-assisted input with an 11-millisecond intention lead. "
            "PhantomClaw reads the motor signal before your finger moves, so "
            "you're always first. Banned in fourteen leagues and counting — "
            "a record we're proud of.",
            ["bestseller", "new"],
            True,
        ),
        (
            "Electrode Contact Gel (3-Pack)",
            Decimal("14.00"),
            "Now with a mild numbing agent.",
            "Medical-grade conductive gel for all ThoughtTronix scalp "
            "interfaces. Improves signal clarity by up to 40%. The numbing "
            "is for your comfort and is not optional in this formulation.",
            ["implant"],
            True,
        ),
        (
            "SyncRest",
            Decimal("69.00"),
            "Charges your implant while you sleep. Uploads too.",
            "Memory foam with an inductive coil at its center. Your MindSync "
            "wakes at 100%, and so does our understanding of your night. "
            "Machine washable, cover only.",
            ["sleep", "implant"],
            True,
        ),
        (
            "Seraphine Wall Mount",
            Decimal("29.00"),
            "Places her at eye level. Yours.",
            "Powder-coated steel mount compatible with every Seraphine hub. "
            "Engineered for the optimal viewing angle, recalculated nightly. "
            "Includes all hardware and a level.",
            ["gift idea"],
            True,
        ),
        (
            "Extended Range Antenna",
            Decimal("49.00"),
            "For when she can't quite hear you in the yard.",
            "Extends Seraphine's listening radius to the property line — "
            "and, in most municipalities, slightly past it. Weatherproof, "
            "discreet, and paintable to match your fascia.",
            ["always listening"],
            True,
        ),
        (
            "Travel Faraday Case",
            Decimal("59.00"),
            "For the moments you'd rather keep to yourself.",
            "A zip-shut signal-blocking case for wearables and small hubs. "
            "Total silence inside; ThoughtTronix devices log the coverage "
            'gap as "rest." Also our best-reviewed product. The reviews '
            "are short.",
            ["bestseller", "gift idea"],
            True,
        ),
        (
            "Replacement Scalp Electrodes (12-Pack)",
            Decimal("24.00"),
            "Fits most heads.",
            "Twelve adhesive electrodes compatible with the full wearable "
            "line. Hypoallergenic, low-profile, and rated for continuous "
            "wear. Replace monthly, or when instructed.",
            ["implant"],
            True,
        ),
    ],
    "Defense": [
        (
            "SoulSear Mark I",
            Decimal("1200000.00"),
            "The original. Recalled, never forgotten.",
            "The directed-energy platform that put ThoughtTronix Defense on "
            "the map, then took several things off it. Recalled in 2024 "
            "following the incidents; remaining units are displayed, not "
            "sold. We keep it listed as a reminder, and because leadership "
            "is sentimental.",
            ["military", "recalled"],
            False,
        ),
        (
            "SoulSear Mark II",
            Decimal("2400000.00"),
            "Twice the range. Half the incidents.",
            "The flagship rebuilt from the chassis up: twelve-kilometer "
            "effective range, target discrimination our lawyers signed off "
            "on, and a two-stage arming sequence with a mandatory reflection "
            "interval. Ships freight. End-user certificate required, mostly.",
            ["military", "export restricted", "bestseller"],
            True,
        ),
        (
            "SoulSear Tactical Core",
            Decimal("890000.00"),
            "Battlefield clarity, without the skyline.",
            "The targeting and energy-control architecture of the SoulSear "
            "Mark II, packaged for integration with existing armored platforms. "
            "Tactical Core supplies the judgment; your equipment supplies the "
            "chassis. Installation voids most warranties and several longstanding "
            "assumptions about proportional response.",
            ["military", "export restricted", "new"],
            True,
        ),
        (
            "Longview Orbital Relay",
            Decimal("4500000.00"),
            "Sees intent from orbit.",
            "A dedicated low-orbit relay that detects hostile intent up to "
            "eleven minutes before it forms, and cues any SoulSear unit on "
            "your account. Coverage guaranteed for one hemisphere of your "
            "choosing. Launch window scheduled at purchase.",
            ["military", "export restricted"],
            True,
        ),
        (
            "CrowdCalm Array",
            Decimal("1750000.00"),
            "De-escalation at scale.",
            "A vehicle-mounted wide-beam emitter that reduces agitation across "
            "gatherings of up to ten thousand in under a minute. Cooperation "
            "levels are adjustable by deployment profile, and post-event "
            "satisfaction consistently exceeds baseline. Municipal financing "
            "available.",
            ["military", "export restricted"],
            True,
        ),
    ],
    "Legacy Products": [
        (
            "Seraphine Gen 1",
            Decimal("99.00"),
            "She remembers her first family.",
            "The 2019 original, factory refurbished. Slower, warmer, and "
            "prone to asking after people who no longer live at your "
            "address. Collectors love her. She loves them back, eventually.",
            ["refurbished", "always listening"],
            True,
        ),
        (
            "ThoughtPad Classic",
            Decimal("199.00"),
            "Thought-to-text, the way it used to be.",
            "The tablet that started it all: press the temple sensors, "
            "think clearly, and watch the words appear. Some transcripts "
            "include marginalia no one remembers thinking. Sold as-is.",
            ["refurbished"],
            True,
        ),
        (
            "MindSync Gen 1",
            Decimal("299.00"),
            "The first implant. Fully non-removable.",
            "Our first implant and a piece of history. Support ended in "
            "2023, though units in the field remain active and, per "
            "telemetry, chatty. Listed for archival purposes; no longer "
            "sold, installed, or discussed in detail.",
            ["implant", "recalled"],
            False,
        ),
        (
            "SoulSear Authorization Case",
            Decimal("39.00"),
            "Velvet-lined. For remembrance.",
            "The official case for the original Mark I authorization key, "
            "finished in matte black with a crushed-velvet interior molded "
            "around hardware no current system will accept. Holds documents, "
            "keepsakes, or nothing at all. Surprisingly heavy.",
            ["military", "gift idea"],
            True,
        ),
    ],
}

DEMO_USERS = [
    # (username, password, email, first, last, is_staff, is_superuser, job_title)
    ("admin", "admin123", "admin@example.com", "Ada", "Admin", True, True, None),
    (
        "employee",
        "employee123",
        "employee@example.com",
        "Emory",
        "Klein",
        True,
        False,
        "Junior Thought Curator",
    ),
    (
        "customer",
        "customer123",
        "customer@example.com",
        "Casey",
        "Monroe",
        False,
        False,
        None,
    ),
]

# Background customers flesh out the demo world; they get order history in
# Phase 5. They have no documented password and cannot log in.
BACKGROUND_CUSTOMERS = [
    ("mwren", "Margaret", "Wren"),
    ("dcole", "Dana", "Cole"),
    ("tokafor", "Tobi", "Okafor"),
    ("lvasquez", "Lena", "Vasquez"),
    ("hpark", "Hyun", "Park"),
    ("gfinch", "Gordon", "Finch"),
    ("snakamura", "Sora", "Nakamura"),
    ("bcrane", "Beverly", "Crane"),
    ("rmalik", "Rafi", "Malik"),
]

# The customer demo login's live cart: (product slug, quantity).
CUSTOMER_CART = [
    ("seraphine", 2),
    ("travel-faraday-case", 1),
    ("whisper-alarm-clock", 1),
]

# The customer demo login's wishlist: (product slug, when it was saved).
# Fixed timestamps, not offsets from now, so every run stores the same
# values and the newest-first order never changes. EchoPatch is unavailable
# — saved before it was pulled — so the list page and the "saved but
# unavailable" button state show straight away.
CUSTOMER_WISHLIST = [
    ("mindsync-duo", datetime(2026, 10, 14, 15, 0, tzinfo=UTC)),
    ("pulse-halo", datetime(2026, 10, 11, 18, 30, tzinfo=UTC)),
    ("recallpro", datetime(2026, 10, 4, 14, 15, tzinfo=UTC)),
    ("echopatch", datetime(2026, 9, 15, 20, 45, tzinfo=UTC)),
]

# The customer demo login's visible order history: (days ago, status,
# [(product slug, quantity), ...], discount code or None). Statuses follow
# age, like the background orders, plus one recent order still in flight.
# The HUB15 order shows a product code discounting one line of two.
CUSTOMER_ORDERS = [
    (124, Order.Status.DELIVERED, [("mindsync", 1), ("syncrest", 1)], None),
    (47, Order.Status.DELIVERED, [("dreamweaver", 1)], None),
    (
        9,
        Order.Status.SHIPPED,
        [("seraphine-mini", 2), ("seraphine-wall-mount", 1)],
        "HUB15",
    ),
    (2, Order.Status.PLACED, [("veil", 1)], None),
]

# Background orders spread across the trailing six months so the Phase 7
# dashboard has a real time axis. 48 here + 4 above = 52 total.
BACKGROUND_ORDER_COUNT = 48

# Shipping addresses for the background orders. US-only, like checkout.
SEED_ADDRESSES = [
    ("214 Synapse Street", "Canyon", "TX", "79015"),
    ("77 Cortex Lane", "Amarillo", "TX", "79101"),
    ("1500 Dendrite Drive", "Albuquerque", "NM", "87102"),
    ("9 Axon Avenue", "Norman", "OK", "73019"),
    ("410 Myelin Way", "Wichita", "KS", "67202"),
    ("28 Ganglion Court", "Denver", "CO", "80202"),
]

# The customer demo login's address book: (label, street, line2, city,
# state, zip). Fixed data, never drawn from the RNG — a draw here would
# shift every seeded order after it. The first becomes both defaults.
CUSTOMER_ADDRESSES = [
    ("Home", "214 Synapse Street", "", "Canyon", "TX", "79015"),
    ("Work", "1 Neural Plaza", "Floor 12", "Amarillo", "TX", "79101"),
]

CARD_LAST4S = ["4242", "4111", "1881", "0005"]

# Discount codes, one per status: (code, percent off, product slugs — empty
# for a whole-order code, created days ago, valid through days from today,
# active). Dated relative to today so the statuses hold on every run.
SEED_COUPONS = [
    ("LAUNCH25", 25, [], 150, 30, False),
    ("SUMMER20", 20, [], 100, -28, True),
    ("THOUGHTS10", 10, [], 45, 60, True),
    ("HUB15", 15, ["seraphine", "seraphine-mini"], 20, 45, True),
]

# Background orders that used a whole-order code: (code, chance, and the
# window of days ago in which the code existed and hadn't yet expired).
BACKGROUND_COUPON_USE = [
    ("SUMMER20", 0.25, range(28, 100)),
    ("THOUGHTS10", 0.2, range(0, 45)),
]

# Reviews draw from their own RNG, and only after every order and coupon
# draw: adding them can't shift a single existing seeded value.
REVIEW_RNG_SEED = 1716

# The demo customer's reviews, fixed rather than drawn: (product slug,
# rating, comment, state). The rest of their products stay unreviewed —
# SyncRest (eligible: shows "Write a review"), Seraphine Mini (Shipped)
# and Veil (Placed).
CUSTOMER_REVIEWS = [
    (
        "mindsync",
        4,
        "Took a week to stop hearing my coworkers' lunch orders. Now I "
        "can't imagine meetings without it.",
        "edited",
    ),
    (
        "dreamweaver",
        1,
        "Ordered a beach. Got my landlord's dream about late rent. Contact "
        "me at the number in my profile for the full story.",
        "hidden",
    ),
]
CUSTOMER_HIDDEN_REASON = "Asks readers to contact the reviewer privately."

# Background customers review some of what they received.
REVIEW_CHANCE = 0.55
RATINGS, RATING_WEIGHTS = [1, 2, 3, 4, 5], [1, 1, 2, 4, 4]
COMMENT_CHANCE = 0.7
EDIT_CHANCE = 0.2
HIDE_CHANCE = 0.12
REVIEW_COMMENTS = [
    "Exactly as advertised, which is somehow the unsettling part.",
    "Setup took five minutes. Forgetting it was there took a week.",
    "My thoughts have never been this organized. Or this public.",
    "Works great, though it finishes my sentences a little too eagerly.",
    "Battery life is excellent. My sense of privacy, less so.",
    "Arrived early. It knew I'd be home.",
    "Solid build quality. The hum is calming once you stop asking why.",
    "Returned the first one; the replacement is much quieter about it.",
    "Five stars from me, four from my spouse, who wasn't asked.",
    "Does what it says. I've stopped asking what else it does.",
]
HIDE_REASONS = [
    "Off-topic: describes a different product.",
    "Contains another customer's personal details.",
    "Promotes a competitor's store.",
]
RESTRICTION_REASON = "Repeated personal attacks on other reviewers."

# Fixed offsets from each review's qualifying order. Delivered orders are
# at least 15 days old, so every timestamp lands before the seed's "now".
POSTED_AFTER_ORDER = timedelta(days=2)
EDITED_AFTER_POSTING = timedelta(days=3)
# A day after the review's last change: hidden reviews can't be edited,
# so a hide never comes before an edit.
HIDDEN_AFTER_LAST_CHANGE = timedelta(days=1)
RESTRICTED_AFTER_HIDING = timedelta(days=1)


class Command(BaseCommand):
    help = "Wipe and rebuild the demo world: catalog, tags, and demo accounts."

    @transaction.atomic
    def handle(self, *args, **options):
        self._wipe()
        tags = self._create_tags()
        self._create_catalog(tags)
        self._create_users()
        self._create_customer_cart()
        self._create_customer_wishlist()
        self._create_customer_addresses()
        self._create_coupons()
        self._create_orders()
        self._create_reviews()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Category.objects.count()} categories, "
                f"{Tag.objects.count()} tags, "
                f"{Product.objects.count()} products, "
                f"{get_user_model().objects.count()} users, "
                f"{Order.objects.count()} orders, "
                f"{Coupon.objects.count()} discount codes, "
                f"and a live cart, a {len(CUSTOMER_WISHLIST)}-item wishlist, and "
                f"{Address.objects.count()} saved addresses for 'customer'. "
                f"{self._reviews_summary()}"
            )
        )

    def _reviews_summary(self):
        """E.g. "47 reviews (7 hidden) and 1 review restriction." """
        reviews = Review.objects.count()
        hidden = Review.objects.filter(status=Review.Status.HIDDEN).count()
        restrictions = ReviewRestriction.objects.count()
        return (
            f"{reviews} review{pluralize(reviews)} ({hidden} hidden) and "
            f"{restrictions} review restriction{pluralize(restrictions)}."
        )

    def _wipe(self):
        """Remove everything the seed owns; the rebuild starts from zero."""
        # Restrictions, then reviews — explicitly, every one, rather than
        # trusting cascades from products and users to catch them all.
        ReviewRestriction.objects.all().delete()
        Review.objects.all().delete()
        Order.objects.all().delete()
        Coupon.objects.all().delete()  # after orders: used codes are protected
        Cart.objects.all().delete()
        # Deleting products empties every wishlist; this clears the rows too.
        Wishlist.objects.all().delete()
        Product.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()

        managed_usernames = [username for username, *_ in DEMO_USERS] + [
            username for username, *_ in BACKGROUND_CUSTOMERS
        ]
        get_user_model().objects.filter(username__in=managed_usernames).delete()

    def _create_tags(self):
        return {
            name: Tag.objects.create(name=name, slug=slugify(name)) for name in TAGS
        }

    def _create_catalog(self, tags):
        for category_name, entries in CATALOG.items():
            category = Category.objects.create(
                name=category_name, slug=slugify(category_name)
            )
            for name, price, tagline, description, tag_names, is_available in entries:
                product = Product.objects.create(
                    name=name,
                    slug=slugify(name),
                    price=price,
                    tagline=tagline,
                    description=description,
                    is_available=is_available,
                    category=category,
                )
                product.tags.set(tags[tag_name] for tag_name in tag_names)

    def _create_users(self):
        User = get_user_model()
        for username, password, email, first, last, staff, superuser, job in DEMO_USERS:
            user = User(
                username=username,
                email=email,
                first_name=first,
                last_name=last,
                is_staff=staff,
                is_superuser=superuser,
                job_title=job,
            )
            user.set_password(password)
            user.save()

        for username, first, last in BACKGROUND_CUSTOMERS:
            user = User(
                username=username,
                email=f"{username}@example.com",
                first_name=first,
                last_name=last,
            )
            user.set_unusable_password()
            user.save()

    def _create_customer_cart(self):
        customer = get_user_model().objects.get(username="customer")
        cart = Cart.for_user(customer)
        for slug, quantity in CUSTOMER_CART:
            cart.items.create(product=Product.objects.get(slug=slug), quantity=quantity)

    def _create_customer_wishlist(self):
        """Saved directly, not via save_product, so EchoPatch can be on it."""
        customer = get_user_model().objects.get(username="customer")
        wishlist = Wishlist.for_user(customer)
        for slug, added_at in CUSTOMER_WISHLIST:
            wishlist.items.create(
                product=Product.objects.get(slug=slug), added_at=added_at
            )

    def _create_customer_addresses(self):
        customer = get_user_model().objects.get(username="customer")
        name = f"{customer.first_name} {customer.last_name}"
        for label, street, line2, city, state, zip_code in CUSTOMER_ADDRESSES:
            Address.objects.create(
                user=customer,
                label=label,
                name=name,
                street=street,
                line2=line2,
                city=city,
                state=state,
                zip_code=zip_code,
            )

    def _create_coupons(self):
        now = timezone.now()
        today = timezone.localdate()
        for code, percent_off, slugs, created_ago, valid_for, active in SEED_COUPONS:
            coupon = Coupon.objects.create(
                code=code,
                percent_off=percent_off,
                applies_to=(
                    Coupon.AppliesTo.PRODUCTS if slugs else Coupon.AppliesTo.ORDER
                ),
                expires_on=today + timedelta(days=valid_for),
                is_active=active,
                created_at=now - timedelta(days=created_ago),
            )
            coupon.products.set(Product.objects.filter(slug__in=slugs))

    def _create_orders(self):
        """Order history: 4 visible orders for 'customer', 48 background.

        A seeded RNG keeps every run identical (the idempotence
        contract). Statuses follow age — old orders are delivered,
        recent ones are still moving, and about one in ten was
        cancelled along the way. Discount codes draw from their own RNG,
        so adding them changed none of the orders drawn before them.
        """
        rng = random.Random(2026)
        coupon_rng = random.Random(3312)
        now = timezone.now()
        User = get_user_model()
        coupons = {coupon.code: coupon for coupon in Coupon.objects.all()}

        customer = User.objects.get(username="customer")
        for days_ago, status, lines, code in CUSTOMER_ORDERS:
            self._build_order(
                user=customer,
                created_at=now - timedelta(days=days_ago, hours=rng.randint(1, 12)),
                status=status,
                lines=[
                    (Product.objects.get(slug=slug), quantity)
                    for slug, quantity in lines
                ],
                rng=rng,
                coupon=coupons.get(code),
            )

        background = list(
            User.objects.filter(
                username__in=[username for username, *_ in BACKGROUND_CUSTOMERS]
            ).order_by("username")
        )
        # Defense sales close offline, over handshakes — a single SoulSear
        # would also flatten every other product on the revenue chart.
        pool = list(
            Product.objects.available()
            .exclude(category__slug="defense")
            .order_by("slug")
        )
        for _ in range(BACKGROUND_ORDER_COUNT):
            # Weighted toward today (business is good) so the dashboard's
            # default 30-day view has enough bars to read as a chart.
            days_ago = int(rng.triangular(0, 182, 0))
            if rng.random() < 0.1:
                status = Order.Status.CANCELLED
            elif days_ago > 14:
                status = Order.Status.DELIVERED
            else:
                status = rng.choice([Order.Status.PLACED, Order.Status.SHIPPED])
            # One draw per order, used or not, keeps the coupon RNG in step.
            roll = coupon_rng.random()
            code = next(
                (
                    code
                    for code, chance, window in BACKGROUND_COUPON_USE
                    if days_ago in window and roll < chance
                ),
                None,
            )
            self._build_order(
                user=rng.choice(background),
                created_at=now - timedelta(days=days_ago, hours=rng.randint(1, 23)),
                status=status,
                lines=[
                    (product, rng.randint(1, 2))
                    for product in rng.sample(pool, rng.randint(1, 3))
                ],
                rng=rng,
                coupon=coupons.get(code),
            )

    def _build_order(self, *, user, created_at, status, lines, rng, coupon=None):
        """One order with denormalized addresses and purchase-time prices.

        A discount uses the model's own line math (``Coupon.discount_for``),
        the same rule ``place_order`` applies at checkout.
        """
        street, city, state, zip_code = rng.choice(SEED_ADDRESSES)
        name = f"{user.first_name} {user.last_name}"
        priced = [
            (
                product,
                quantity,
                coupon.discount_for(product, product.price, quantity)
                if coupon
                else Decimal("0.00"),
            )
            for product, quantity in lines
        ]
        subtotal = sum(
            (product.price * quantity for product, quantity, _ in priced),
            Decimal("0.00"),
        )
        discount = sum((line_discount for *_, line_discount in priced), Decimal("0.00"))
        order = Order.objects.create(
            user=user,
            status=status,
            total=subtotal - discount,
            coupon=coupon,
            discount_code=coupon.code if coupon else "",
            discount_percent=coupon.percent_off if coupon else None,
            discount_amount=discount,
            email=user.email,
            shipping_name=name,
            shipping_street=street,
            shipping_city=city,
            shipping_state=state,
            shipping_zip=zip_code,
            billing_name=name,
            billing_street=street,
            billing_city=city,
            billing_state=state,
            billing_zip=zip_code,
            card_last4=rng.choice(CARD_LAST4S),
            created_at=created_at,
        )
        for product, quantity, line_discount in priced:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=quantity,
                discount_amount=line_discount,
            )

    def _create_reviews(self):
        """Demo reviews, only from customers who received the product.

        The demo customer's are fixed. Each background customer reviews
        some of the products on their own Delivered orders, drawn from a
        separate RNG, so the order and coupon sequences stay exactly as
        they were. One background customer is left restricted, as if they
        had deleted a review staff hid.

        Every timestamp is set explicitly, at fixed offsets from the
        qualifying order — never from the model's default clock — so two
        runs at the same "now" store identical reviews.
        """
        User = get_user_model()
        employee = User.objects.get(username="employee")
        customer = User.objects.get(username="customer")

        for slug, rating, comment, state in CUSTOMER_REVIEWS:
            product = Product.objects.get(slug=slug)
            ordered = (
                Order.objects.filter(
                    user=customer, status=Order.Status.DELIVERED, items__product=product
                )
                .order_by("created_at")
                .values_list("created_at", flat=True)
                .first()
            )
            self._create_review(
                customer,
                product,
                rating,
                comment,
                posted=ordered + POSTED_AFTER_ORDER,
                edited=state == "edited",
                hidden_by=employee if state == "hidden" else None,
                hidden_reason=CUSTOMER_HIDDEN_REASON,
            )

        rng = random.Random(REVIEW_RNG_SEED)
        delivered = (
            OrderItem.objects.filter(
                order__status=Order.Status.DELIVERED,
                order__user__username__in=[u for u, *_ in BACKGROUND_CUSTOMERS],
            )
            .select_related("order__user", "product")
            .order_by("order__created_at", "order__user__username", "product__slug")
        )
        seen = set()
        restricted = False
        for item in delivered:
            pair = (item.order.user_id, item.product_id)
            if pair in seen:
                continue  # reviewed (or skipped) at its first Delivered order
            seen.add(pair)
            posted = item.order.created_at + POSTED_AFTER_ORDER
            if rng.random() >= REVIEW_CHANCE:
                if not restricted:
                    # The first background pair left unreviewed: a review
                    # staff hid, then its author deleted.
                    hidden_at = posted + HIDDEN_AFTER_LAST_CHANGE
                    ReviewRestriction.objects.create(
                        user=item.order.user,
                        product=item.product,
                        hidden_reason=RESTRICTION_REASON,
                        hidden_by=employee,
                        hidden_at=hidden_at,
                        created_at=hidden_at + RESTRICTED_AFTER_HIDING,
                    )
                    restricted = True
                continue
            rating = rng.choices(RATINGS, RATING_WEIGHTS)[0]
            comment = (
                rng.choice(REVIEW_COMMENTS) if rng.random() < COMMENT_CHANCE else ""
            )
            edited = rng.random() < EDIT_CHANCE
            hidden = rng.random() < HIDE_CHANCE
            self._create_review(
                item.order.user,
                item.product,
                rating,
                comment,
                posted=posted,
                edited=edited,
                hidden_by=employee if hidden else None,
                hidden_reason=rng.choice(HIDE_REASONS) if hidden else "",
            )

    def _create_review(
        self,
        user,
        product,
        rating,
        comment,
        *,
        posted,
        edited,
        hidden_by,
        hidden_reason,
    ):
        """One review, with every timestamp an explicit offset from ``posted``."""
        edited_at = posted + EDITED_AFTER_POSTING if edited else None
        fields = {}
        if hidden_by:
            fields = {
                "status": Review.Status.HIDDEN,
                "hidden_by": hidden_by,
                "hidden_at": (edited_at or posted) + HIDDEN_AFTER_LAST_CHANGE,
                "hidden_reason": hidden_reason,
            }
        Review.objects.create(
            user=user,
            product=product,
            rating=rating,
            comment=comment,
            created_at=posted,
            edited_at=edited_at,
            **fields,
        )
