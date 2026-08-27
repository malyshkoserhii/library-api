from typing import Any

from django.db import transaction
from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing
from user.serializers import UserSerializer


class BorrowingListSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book_title",
            "user_email",
        )
        read_only_fields = ("id",)


class BorrowingDetailSerializer(BorrowingListSerializer):
    book = BookSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date")

    def validate(self, attrs: Any) -> Any:
        book = attrs.get("book")
        if book.inventory < 1:
            raise serializers.ValidationError(
                {"book": f"'{book.title}' is currently out of stock."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data: Any):
        book = validated_data["book"]
        book.inventory -= 1
        book.save()

        borrowing = Borrowing.objects.create(**validated_data)
        return borrowing
