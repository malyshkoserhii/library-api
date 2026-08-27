from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expected_return_date__gt=models.F("borrow_date")),
                name="check_expected_return_date_after_borrow_date",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(actual_return_date__isnull=True)
                    | models.Q(actual_return_date__gte=models.F("borrow_date"))
                ),
                name="check_actual_return_date_after_or_equal_borrow_date",
            ),
        ]

    def clean(self):
        super().clean()

        borrow_date = self.borrow_date or date.today()

        if borrow_date and self.expected_return_date:
            if self.expected_return_date <= borrow_date:
                raise ValidationError(
                    {
                        "expected_return_date": (
                            "Expected return date must be after the borrow date."
                        )
                    }
                )

        if borrow_date and self.actual_return_date:
            if self.actual_return_date < borrow_date:
                raise ValidationError(
                    {
                        "actual_return_date": (
                            "Actual return date cannot be earlier than the borrow date."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user} - {self.book} ({self.borrow_date})"
