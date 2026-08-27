from django.db import models


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = "HARD"
        SOFT = "SOFT"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(choices=CoverType, default=CoverType.HARD, max_length=50)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ("title",)
        constraints = [
            models.UniqueConstraint(
                fields=["title", "author", "cover"],
                name="unique_book_title_author_cover",
            )
        ]

    def __str__(self) -> str:
        return self.title
