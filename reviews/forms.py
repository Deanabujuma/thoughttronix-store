from django import forms

from .models import Review

STAR_CHOICES = [(n, f"{n} star" if n == 1 else f"{n} stars") for n in range(1, 6)]


class ReviewForm(forms.ModelForm):
    """A required 1–5 whole-star rating and an optional, trimmed comment.

    The comment's 2,000-character limit and the trimming come from the
    model field (a ModelForm ``CharField`` strips by default).
    """

    rating = forms.TypedChoiceField(
        choices=STAR_CHOICES,
        coerce=int,
        widget=forms.RadioSelect,
        error_messages={
            "required": "Choose a rating from 1 to 5 stars.",
            "invalid_choice": "Choose a rating from 1 to 5 stars.",
        },
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        labels = {"comment": "Comment (optional)"}
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 5, "class": "textarea w-full"})
        }
