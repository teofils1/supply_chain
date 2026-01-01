"""
API views for the notification system.
"""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from supplychain.models import NotificationLog, NotificationRule
from supplychain.pagination import StandardResultsPagination
from supplychain.serializers import (
    NotificationLogSerializer,
    NotificationRuleSerializer,
)


# Notification Rules
class NotificationRuleListCreateView(generics.ListCreateAPIView):
    """List and create notification rules."""

    serializer_class = NotificationRuleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return NotificationRule.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a notification rule."""

    serializer_class = NotificationRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationRule.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        )


class NotificationRuleToggleView(APIView):
    """Toggle enabled status of a notification rule."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rule = NotificationRule.objects.get(
                pk=pk, user=request.user, deleted_at__isnull=True
            )
        except NotificationRule.DoesNotExist:
            return Response(
                {"detail": "Notification rule not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        rule.enabled = not rule.enabled
        rule.save(update_fields=["enabled"])

        serializer = NotificationRuleSerializer(rule)
        return Response(serializer.data)


# Notification Logs
class NotificationLogListView(generics.ListAPIView):
    """List notification logs for the current user."""

    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        queryset = NotificationLog.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        ).select_related("event", "user", "rule", "escalated_to")

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by channel
        channel_filter = self.request.query_params.get("channel")
        if channel_filter:
            queryset = queryset.filter(channel=channel_filter)

        # Filter unread
        unread_only = self.request.query_params.get("unread")
        if unread_only and unread_only.lower() in ["true", "1", "yes"]:
            queryset = queryset.filter(acknowledged_at__isnull=True)

        return queryset.order_by("-created_at")


class NotificationLogDetailView(generics.RetrieveAPIView):
    """Retrieve a single notification log."""

    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationLog.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        ).select_related("event", "user", "rule")


class NotificationLogAcknowledgeView(APIView):
    """Mark a notification as acknowledged."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = NotificationLog.objects.get(
                pk=pk, user=request.user, deleted_at__isnull=True
            )
        except NotificationLog.DoesNotExist:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if notification.acknowledged_at:
            return Response(
                {"detail": "Notification already acknowledged."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification.acknowledged_at = timezone.now()
        notification.save(update_fields=["acknowledged_at"])

        serializer = NotificationLogSerializer(notification)
        return Response(serializer.data)


class NotificationLogAcknowledgeAllView(APIView):
    """Mark all unread notifications as acknowledged."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = NotificationLog.objects.filter(
            user=request.user, acknowledged_at__isnull=True, deleted_at__isnull=True
        ).update(acknowledged_at=timezone.now())

        return Response({"acknowledged": updated})


class NotificationLogUnreadCountView(APIView):
    """Get count of unread notifications."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = NotificationLog.objects.filter(
            user=request.user, acknowledged_at__isnull=True, deleted_at__isnull=True
        ).count()
        return Response({"unread_count": count})


class NotificationLogRecentView(generics.ListAPIView):
    """Get recent notifications (last 10)."""

    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination for recent notifications

    def get_queryset(self):
        return (
            NotificationLog.objects.filter(
                user=self.request.user, deleted_at__isnull=True
            )
            .select_related("event", "user", "rule")
            .order_by("-created_at")[:10]
        )
