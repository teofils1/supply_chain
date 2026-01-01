"""
Celery tasks for the notification system.

This module contains async tasks for sending notifications via
email, WebSocket, and SMS channels using RabbitMQ as the broker.
"""

import structlog
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(self, event_id: int, user_id: int, rule_id: int = None):
    """
    Send an email notification for an event.

    Args:
        event_id: ID of the Event that triggered the notification
        user_id: ID of the User to notify
        rule_id: Optional ID of the NotificationRule that matched
    """
    from supplychain.models import Event, NotificationLog, NotificationRule
    
    User = get_user_model()

    try:
        event = Event.objects.get(id=event_id)
        user = User.objects.get(id=user_id)
        rule = NotificationRule.objects.get(id=rule_id) if rule_id else None

        # Create notification log entry
        notification_log = NotificationLog.objects.create(
            event=event,
            user=user,
            rule=rule,
            channel="email",
            status="pending",
        )

        # Build email context
        context = {
            "event": event,
            "user": user,
            "severity": event.severity,
            "event_type": event.event_type,
            "description": event.description,
            "timestamp": event.timestamp,
            "metadata": event.metadata or {},
            "frontend_url": settings.FRONTEND_URL if hasattr(settings, "FRONTEND_URL") else "http://localhost:4200",
        }

        # Select template based on severity
        if event.severity == "critical":
            template_name = "notifications/email/alert_critical.html"
            subject = f"🚨 CRITICAL: {event.description}"
        elif event.severity == "high":
            template_name = "notifications/email/alert_high.html"
            subject = f"⚠️ ALERT: {event.description}"
        else:
            template_name = "notifications/email/alert_standard.html"
            subject = f"📋 Notification: {event.description}"

        # Render email content
        try:
            html_message = render_to_string(template_name, context)
        except Exception:
            # Fallback to plain text if template not found
            html_message = None

        plain_message = f"""
Supply Chain Alert

Type: {event.event_type}
Severity: {event.severity.upper()}
Description: {event.description}
Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

---
This is an automated notification from the Supply Chain Tracking System.
        """.strip()

        # Send the email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Update notification log
        notification_log.status = "sent"
        notification_log.sent_at = timezone.now()
        notification_log.save(update_fields=["status", "sent_at"])

        logger.info(
            "email_notification_sent",
            event_id=event_id,
            user_id=user_id,
            user_email=user.email,
            severity=event.severity,
        )

        return {"status": "sent", "notification_id": notification_log.id}

    except User.DoesNotExist:
        logger.error("email_notification_failed", error="User not found", user_id=user_id)
        return {"status": "failed", "error": "User not found"}

    except Exception as exc:
        logger.error(
            "email_notification_failed",
            event_id=event_id,
            user_id=user_id,
            error=str(exc),
        )

        # Update notification log if it was created
        try:
            notification_log.status = "failed"
            notification_log.error_message = str(exc)
            notification_log.save(update_fields=["status", "error_message"])
        except Exception:
            pass

        # Retry the task
        raise self.retry(exc=exc)


@shared_task(bind=True)
def process_event_notifications(self, event_id: int):
    """
    Process an event and send notifications to all matching rules.

    This is the main entry point called when a new event is created.
    It evaluates all notification rules and queues individual notifications.

    Args:
        event_id: ID of the Event to process
    """
    from supplychain.models import Event, NotificationRule

    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        logger.error("process_notifications_failed", error="Event not found", event_id=event_id)
        return {"status": "failed", "error": "Event not found"}

    # Check if this event should trigger notifications based on settings
    should_notify = (
        event.severity in getattr(settings, "NOTIFICATION_ALERT_SEVERITIES", ["critical", "high"])
        or event.event_type in getattr(settings, "NOTIFICATION_CRITICAL_EVENTS", [])
    )

    if not should_notify:
        logger.debug(
            "event_skipped_no_notification",
            event_id=event_id,
            event_type=event.event_type,
            severity=event.severity,
        )
        return {"status": "skipped", "reason": "Event does not match notification criteria"}

    # Find all matching notification rules
    rules = NotificationRule.objects.filter(enabled=True).select_related("user")

    notifications_queued = 0
    for rule in rules:
        if rule.matches_event(event):
            # Queue notifications for each channel in the rule
            for channel in rule.channels:
                if channel == "email":
                    send_email_notification.delay(
                        event_id=event.id,
                        user_id=rule.user.id,
                        rule_id=rule.id,
                    )
                    notifications_queued += 1
                elif channel == "websocket":
                    # WebSocket notifications can be added later
                    pass
                elif channel == "sms":
                    # SMS notifications can be added later
                    pass

    logger.info(
        "event_notifications_processed",
        event_id=event_id,
        event_type=event.event_type,
        severity=event.severity,
        notifications_queued=notifications_queued,
    )

    return {
        "status": "processed",
        "event_id": event_id,
        "notifications_queued": notifications_queued,
    }


@shared_task
def check_escalations():
    """
    Periodic task to check for unacknowledged critical notifications
    and escalate them to administrators.

    This task should be scheduled to run every few minutes via Celery Beat.
    """
    from supplychain.models import NotificationLog, UserProfile

    timeout_minutes = getattr(settings, "NOTIFICATION_ESCALATION_TIMEOUT", 30)
    cutoff_time = timezone.now() - timezone.timedelta(minutes=timeout_minutes)

    # Find unacknowledged critical notifications past the timeout
    unacknowledged = NotificationLog.objects.filter(
        status="sent",
        escalated=False,
        sent_at__lt=cutoff_time,
        event__severity="critical",
    ).select_related("event", "user")

    escalated_count = 0
    for notification in unacknowledged:
        # Find admin users to escalate to
        admin_profiles = UserProfile.objects.filter(active_role="Admin").select_related("user")

        for profile in admin_profiles:
            if profile.user.id != notification.user.id:  # Don't escalate to self
                # Queue escalation email
                send_email_notification.delay(
                    event_id=notification.event.id,
                    user_id=profile.user.id,
                )

                # Mark original notification as escalated
                notification.escalated = True
                notification.escalated_to = profile.user
                notification.escalated_at = timezone.now()
                notification.save(update_fields=["escalated", "escalated_to", "escalated_at"])

                escalated_count += 1
                break  # Only escalate to one admin

    logger.info("escalation_check_completed", escalated_count=escalated_count)

    return {"escalated_count": escalated_count}
