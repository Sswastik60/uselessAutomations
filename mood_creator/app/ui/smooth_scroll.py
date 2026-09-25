"""Liquid-smooth momentum scrolling engine for Qt/PySide6 widgets.

Provides Apple/macOS-quality fluid scrolling with kinetic momentum accumulation,
OutCubic easing interpolation, and sub-pixel resolution for QScrollArea,
QTableWidget, QListWidget, and any QAbstractScrollArea.
"""

from typing import Optional
from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QObject,
    Property,
    QPropertyAnimation,
    Qt,
)
from PySide6.QtWidgets import QAbstractScrollArea, QScrollBar


class SmoothScrollFilter(QObject):
    """Event filter that intercepts wheel events on a scroll area's viewport

    and animates the scroll position with a smooth momentum curve.
    """

    def __init__(
        self,
        scroll_area: QAbstractScrollArea,
        step_size: float = 92.0,
        duration: int = 180,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent or scroll_area)
        self.scroll_area = scroll_area
        self.viewport = scroll_area.viewport()
        self.v_bar: QScrollBar = scroll_area.verticalScrollBar()
        self.h_bar: QScrollBar = scroll_area.horizontalScrollBar()
        self.base_step_size = step_size
        self.base_duration = duration

        # Target offsets for accumulation
        self._target_v = float(self.v_bar.value())
        self._target_h = float(self.h_bar.value())

        # Vertical animation
        self._anim_v = QPropertyAnimation(self, b"v_scroll_pos", self)
        self._anim_v.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Horizontal animation
        self._anim_h = QPropertyAnimation(self, b"h_scroll_pos", self)
        self._anim_h.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Sync target when user drags the scrollbar handle directly
        self.v_bar.sliderMoved.connect(self._on_v_slider_moved)
        self.h_bar.sliderMoved.connect(self._on_h_slider_moved)
        self.v_bar.actionTriggered.connect(self._on_v_action_triggered)
        self.h_bar.actionTriggered.connect(self._on_h_action_triggered)

        # Install on viewport
        self.viewport.installEventFilter(self)

    def _on_v_slider_moved(self, val: int) -> None:
        self._anim_v.stop()
        self._target_v = float(val)

    def _on_h_slider_moved(self, val: int) -> None:
        self._anim_h.stop()
        self._target_h = float(val)

    def _on_v_action_triggered(self, action: int) -> None:
        if action in (
            QScrollBar.SliderAction.SliderMove,
            QScrollBar.SliderAction.SliderPageStepAdd,
            QScrollBar.SliderAction.SliderPageStepSub,
            QScrollBar.SliderAction.SliderToMinimum,
            QScrollBar.SliderAction.SliderToMaximum,
        ):
            self._anim_v.stop()
            self._target_v = float(self.v_bar.value())

    def _on_h_action_triggered(self, action: int) -> None:
        if action in (
            QScrollBar.SliderAction.SliderMove,
            QScrollBar.SliderAction.SliderPageStepAdd,
            QScrollBar.SliderAction.SliderPageStepSub,
            QScrollBar.SliderAction.SliderToMinimum,
            QScrollBar.SliderAction.SliderToMaximum,
        ):
            self._anim_h.stop()
            self._target_h = float(self.h_bar.value())

    @Property(float)
    def v_scroll_pos(self) -> float:
        return float(self.v_bar.value())

    @v_scroll_pos.setter
    def v_scroll_pos(self, pos: float) -> None:
        self.v_bar.setValue(int(round(pos)))

    @Property(float)
    def h_scroll_pos(self) -> float:
        return float(self.h_bar.value())

    @h_scroll_pos.setter
    def h_scroll_pos(self, pos: float) -> None:
        self.h_bar.setValue(int(round(pos)))

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        viewport = getattr(self, "viewport", None)
        if viewport is not None and obj is viewport and event.type() == QEvent.Type.Wheel:
            # 1. Check for precision touchpad (pixelDelta)
            pixel_delta = event.pixelDelta()
            if not pixel_delta.isNull():
                self._anim_v.stop()
                self._anim_h.stop()
                if pixel_delta.y() != 0 and self.v_bar.maximum() > self.v_bar.minimum():
                    self.v_bar.setValue(self.v_bar.value() - pixel_delta.y())
                    self._target_v = float(self.v_bar.value())
                if pixel_delta.x() != 0 and self.h_bar.maximum() > self.h_bar.minimum():
                    self.h_bar.setValue(self.h_bar.value() - pixel_delta.x())
                    self._target_h = float(self.h_bar.value())
                event.accept()
                return True

            # 2. Check for mouse wheel notches (angleDelta)
            angle_delta = event.angleDelta()
            modifiers = event.modifiers()
            is_horizontal = (modifiers & Qt.KeyboardModifier.ShiftModifier) or (
                angle_delta.x() != 0 and angle_delta.y() == 0
            )

            delta = angle_delta.x() if is_horizontal else angle_delta.y()
            if delta == 0:
                return False

            bar = self.h_bar if is_horizontal else self.v_bar
            anim = self._anim_h if is_horizontal else self._anim_v

            # Pass through if the scrollbar has no range to scroll
            if bar.maximum() <= bar.minimum():
                return False

            # Check if reduce motion is globally requested
            from app.ui.animation_manager import AnimationManager
            if AnimationManager.reduce_motion:
                return False

            # Convert 120-unit ticks into proportional step distance
            notch_count = delta / 120.0
            step = self.base_step_size

            # Target accumulation for fluid continuous velocity
            current_target = self._target_h if is_horizontal else self._target_v

            if anim.state() != QAbstractAnimation.State.Running:
                current_target = float(bar.value())

            # Accumulate target distance
            new_target = current_target - (notch_count * step)
            clamped_target = max(float(bar.minimum()), min(float(bar.maximum()), new_target))

            if is_horizontal:
                self._target_h = clamped_target
            else:
                self._target_v = clamped_target

            # Dynamic duration: 150ms for a single notch, scaling up to 230ms for rapid scrolling
            distance = abs(clamped_target - float(bar.value()))
            duration = int(min(230, max(150, self.base_duration + distance * 0.22)))

            anim.stop()
            anim.setDuration(duration)
            anim.setStartValue(float(bar.value()))
            anim.setEndValue(clamped_target)
            anim.start()

            event.accept()
            return True

        return super().eventFilter(obj, event)


def install_smooth_scroll(
    scroll_area: QAbstractScrollArea,
    step_size: float = 92.0,
    duration: int = 180,
) -> SmoothScrollFilter:
    """Convenience helper to attach smooth momentum scrolling to any scroll area."""
    return SmoothScrollFilter(scroll_area, step_size=step_size, duration=duration)
