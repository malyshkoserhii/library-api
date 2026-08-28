from datetime import date
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List borrowings",
        description="Retrieve a list of borrowings. "
        "Non-staff users only see their own borrowings.",
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=bool,
                description="Filter active (not returned yet) borrowings "
                "(e.g. ?is_active=true)",
            ),
            OpenApiParameter(
                name="user_id",
                type=int,
                description="Filter borrowings by user ID "
                "(available for staff users only)",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve borrowing details",
        description="Retrieve detailed information about a specific borrowing by ID.",
    ),
    create=extend_schema(
        summary="Create a new borrowing",
        description="Borrow a book. Decrements the book's inventory by 1.",
    ),
)
class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.all().select_related("book", "user")
    permission_classes = (IsAuthenticated,)
    serializer_class = BorrowingListSerializer

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")

        # Divide access: A simple user can see only own borrowings
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        elif user_id:
            # Admin can filter by using any user_id
            queryset = queryset.filter(user_id=user_id)

        # Filtering by is_active
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "create":
            return BorrowingCreateSerializer
        if self.action == "return_borrowing":
            return BorrowingReturnSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Return a borrowed book",
        description="Closes the borrowing record, sets actual_return_date to today, "
        "and increases book inventory by 1.",
        responses={
            200: BorrowingDetailSerializer,
            400: {"description": "Borrowing is already returned."},
        },
    )
    @action(methods=["POST"], detail=True, url_path="return")
    @transaction.atomic
    def return_borrowing(self, request, pk=None):
        """Endpoint for returning a borrowed book"""

        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing.actual_return_date = date.today()
        borrowing.save()

        book = borrowing.book
        book.inventory += 1
        book.save()

        serializer = BorrowingDetailSerializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)
