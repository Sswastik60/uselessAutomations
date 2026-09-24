from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult


class NotificationAction(BaseAction):
    """Show a system desktop notification or log notice."""

    PARAM_SCHEMA = {
        "title": {"type": "string", "label": "Title", "default": "Automation Hub"},
        "message": {"type": "string", "label": "Message Content", "required": True},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title", f"Mode: {context.mode_name}")
        message = self.params.get("message", "")

        context.logger.info(f"NOTIFICATION [{title}]: {message}")

        # Try notification service if registered
        notif_svc = context.get_service("notification_service")
        if notif_svc and hasattr(notif_svc, "show_notification"):
            try:
                notif_svc.show_notification(title, message)
            except Exception as e:
                context.logger.warning(f"Notification service error: {e}")

        return ActionResult(success=True, message=f"Notification dispatched: '{message}'")


# Register notification action
action_registry.register("notification.show", NotificationAction, category="Notification", display_name="Show Notification")
