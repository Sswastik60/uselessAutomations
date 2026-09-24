import logging
import time
from typing import Callable, Dict, List, Optional
from PySide6.QtCore import QObject, QThread, Signal

from app.core.action_registry import action_registry
from app.core.event_bus import event_bus
from app.core.execution_context import AutomationContext
from app.models.action import ActionConfig
from app.models.action_result import ActionResult
from app.models.mode import Mode

logger = logging.getLogger(__name__)


class EngineSignals(QObject):
    """Qt signals for emitting engine events safely to UI components."""

    mode_started = Signal(str, str)  # mode_id, mode_name
    action_started = Signal(int, int, str)  # step_idx, total_steps, action_display_name
    action_completed = Signal(int, int, str, ActionResult)  # step_idx, total_steps, action_name, result
    mode_progress = Signal(float, str)  # percent_0_to_100, current_status_message
    mode_completed = Signal(str, str, float)  # mode_id, mode_name, total_duration
    mode_failed = Signal(str, str, str)  # mode_id, mode_name, error_message
    mode_cancelled = Signal(str, str)  # mode_id, mode_name


class AutomationWorker(QThread):
    """QThread worker to execute Mode automation sequences off the main Qt UI thread."""

    def __init__(
        self,
        mode: Mode,
        services: Dict[str, Any],
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.mode = mode
        self.services = services
        self.signals = EngineSignals()
        self.context = AutomationContext(
            mode_id=mode.id,
            mode_name=mode.name,
            services=services,
            logger=logger,
        )

    def cancel(self) -> None:
        """Request immediate execution cancellation."""
        self.context.request_cancellation()

    def run(self) -> None:
        """Thread execution loop."""
        start_time = time.time()
        total_steps = len(self.mode.actions)
        
        logger.info(f"Starting execution of Mode '{self.mode.name}' ({total_steps} actions)")
        self.signals.mode_started.emit(self.mode.id, self.mode.name)
        event_bus.publish("mode_started", mode_id=self.mode.id, mode_name=self.mode.name)

        if total_steps == 0:
            duration = round(time.time() - start_time, 3)
            self.signals.mode_completed.emit(self.mode.id, self.mode.name, duration)
            event_bus.publish("mode_completed", mode_id=self.mode.id, mode_name=self.mode.name, duration=duration)
            return

        for idx, action_config in enumerate(self.mode.actions):
            if self.context.is_cancelled():
                logger.warning(f"Execution of '{self.mode.name}' cancelled by user at step {idx + 1}")
                self.signals.mode_cancelled.emit(self.mode.id, self.mode.name)
                event_bus.publish("mode_cancelled", mode_id=self.mode.id, mode_name=self.mode.name)
                return

            display_name = action_config.get_display_name()
            step_num = idx + 1
            progress_pct = ((idx) / total_steps) * 100.0

            self.signals.action_started.emit(step_num, total_steps, display_name)
            self.signals.mode_progress.emit(progress_pct, f"Running: {display_name}")
            event_bus.publish(
                "action_started",
                step_idx=step_num,
                total_steps=total_steps,
                action_name=display_name,
            )

            result = self._execute_action_with_policy(action_config)
            self.context.results_history.append(result)

            self.signals.action_completed.emit(step_num, total_steps, display_name, result)
            event_bus.publish(
                "action_completed",
                step_idx=step_num,
                total_steps=total_steps,
                action_name=display_name,
                result=result,
            )

            if not result.success:
                if action_config.on_failure == "stop":
                    error_msg = f"Action '{display_name}' failed: {result.error or result.message}"
                    logger.error(f"Mode '{self.mode.name}' halted due to failure: {error_msg}")
                    self.signals.mode_failed.emit(self.mode.id, self.mode.name, error_msg)
                    event_bus.publish("mode_failed", mode_id=self.mode.id, mode_name=self.mode.name, error=error_msg)
                    return
                elif action_config.on_failure == "continue":
                    logger.warning(f"Action '{display_name}' failed but failure policy is 'continue'. Proceeding...")

        duration = round(time.time() - start_time, 3)
        self.signals.mode_progress.emit(100.0, "Completed successfully")
        self.signals.mode_completed.emit(self.mode.id, self.mode.name, duration)
        event_bus.publish("mode_completed", mode_id=self.mode.id, mode_name=self.mode.name, duration=duration)
        logger.info(f"Mode '{self.mode.name}' completed in {duration}s")

    def _execute_action_with_policy(self, action_config: ActionConfig) -> ActionResult:
        """Instantiate action and execute according to retry policy."""
        attempts = 1 + (action_config.retry_count if action_config.on_failure == "retry" else 0)
        last_result = None

        for attempt in range(1, attempts + 1):
            if self.context.is_cancelled():
                return ActionResult(success=False, message="Execution cancelled", error="Cancelled by user")

            try:
                action_obj = action_registry.create_action(action_config.type, action_config.params)
                step_start = time.time()
                result = action_obj.execute(self.context)
                result.duration = round(time.time() - step_start, 3)

                if result.success or attempt == attempts:
                    return result
                
                logger.warning(f"Action '{action_config.type}' attempt {attempt} failed: {result.message}. Retrying...")
                time.sleep(0.5)
            except Exception as ex:
                logger.error(f"Unhandled exception running action '{action_config.type}': {ex}", exc_info=True)
                last_result = ActionResult(
                    success=False,
                    message=f"Action exception: {str(ex)}",
                    error=str(ex),
                )
                if attempt == attempts:
                    return last_result
                time.sleep(0.5)

        return last_result or ActionResult(success=False, message="Action failed", error="Unknown execution failure")


class AutomationEngine:
    """Engine interface for initiating mode executions."""

    def __init__(self, services: Optional[Dict[str, Any]] = None):
        self.services = services or {}
        self._current_worker: Optional[AutomationWorker] = None

    def execute_mode(self, mode: Mode) -> AutomationWorker:
        """Launch background worker thread to run a Mode."""
        if self.is_running():
            raise RuntimeError(f"Engine is already executing mode '{self._current_worker.mode.name}'")

        worker = AutomationWorker(mode, self.services)
        self._current_worker = worker
        
        # Cleanup worker reference when done
        worker.finished.connect(self._on_worker_finished)
        worker.start()
        return worker

    def cancel_current_mode(self) -> bool:
        """Cancel current running mode execution if active."""
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.cancel()
            return True
        return False

    def is_running(self) -> bool:
        """Check if an automation worker is currently running."""
        return self._current_worker is not None and self._current_worker.isRunning()

    def get_current_mode(self) -> Optional[Mode]:
        """Return the currently executing mode if running."""
        if self.is_running() and self._current_worker:
            return self._current_worker.mode
        return None

    def _on_worker_finished(self) -> None:
        """Reset current worker handle."""
        self._current_worker = None
