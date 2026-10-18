from django import forms
from django.utils import timezone

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

    def save(self, commit=True):
        """Save, marking an existing review edited only on a real change.

        ``has_changed`` compares the stored values with the submission as
        the fields clean it — the rating as a whole number, the comment
        trimmed — so resaving the same words never counts as an edit.
        ``created_at`` is never touched, so the review keeps its place.
        """
        if self.instance.pk and self.has_changed():
            self.instance.edited_at = timezone.now()
        return super().save(commit)
