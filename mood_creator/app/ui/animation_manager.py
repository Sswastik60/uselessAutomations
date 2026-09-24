"""Centralized Animation Manager utility using Qt's Animation Framework."""

import logging
from typing import Callable, Optional
from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from app.ui.styles.design_tokens import AnimationDuration, AnimationEasing

logger = logging.getLogger(__name__)


class AnimationManager:
    """Central manager for UI animations across the application."""

    reduce_motion: bool = False

    @classmethod
    def set_reduce_motion(cls, enabled: bool) -> None:
        """Globally enable or disable reduce motion mode for accessibility."""
        cls.reduce_motion = enabled
        logger.info(f"Reduce motion set to: {enabled}")

    @classmethod
    def fade_in(
        cls,
        widget: QWidget,
        duration: int = AnimationDuration.NORMAL,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> Optional[QPropertyAnimation]:
        """Fade in a widget using QGraphicsOpacityEffect."""
        if cls.reduce_motion:
            widget.show()
            if on_finished:
                on_finished()
            return None

        widget.show()
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(AnimationEasing.FAST_OUT)

        if on_finished:
            anim.finished.connect(on_finished)

        # Retain reference on widget to prevent premature GC
        widget._active_fade_anim = anim  # type: ignore
        anim.start()
        return anim

    @classmethod
    def fade_out(
        cls,
        widget: QWidget,
        duration: int = AnimationDuration.NORMAL,
        hide_on_finish: bool = True,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> Optional[QPropertyAnimation]:
        """Fade out a widget using QGraphicsOpacityEffect."""
        if cls.reduce_motion:
            if hide_on_finish:
                widget.hide()
            if on_finished:
                on_finished()
            return None

        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(effect.opacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(AnimationEasing.FAST_OUT)

        def _on_done():
            if hide_on_finish:
                widget.hide()
            if on_finished:
                on_finished()

        anim.finished.connect(_on_done)

        widget._active_fade_anim = anim  # type: ignore
        anim.start()
        return anim

    @classmethod
    def slide_in(
        cls,
        widget: QWidget,
        direction: str = "bottom",
        offset: int = 20,
        duration: int = AnimationDuration.NORMAL,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> Optional[QParallelAnimationGroup]:
        """Slide and fade in a widget smoothly from a direction (left, right, top, bottom)."""
        if cls.reduce_motion:
            widget.show()
            if on_finished:
                on_finished()
            return None

        widget.show()
        pos = widget.pos()

        start_pos = QPoint(pos.x(), pos.y())
        if direction == "bottom":
            start_pos.setY(pos.y() + offset)
        elif direction == "top":
            start_pos.setY(pos.y() - offset)
        elif direction == "left":
            start_pos.setX(pos.x() - offset)
        elif direction == "right":
            start_pos.setX(pos.x() + offset)

        pos_anim = QPropertyAnimation(widget, b"pos")
        pos_anim.setDuration(duration)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(pos)
        pos_anim.setEasingCurve(AnimationEasing.SMOOTH)

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        fade_anim = QPropertyAnimation(effect, b"opacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(AnimationEasing.FAST_OUT)

        group = QParallelAnimationGroup()
        group.addAnimation(pos_anim)
        group.addAnimation(fade_anim)

        if on_finished:
            group.finished.connect(on_finished)

        widget._active_slide_group = group  # type: ignore
        group.start()
        return group

    @classmethod
    def pulse(
        cls,
        widget: QWidget,
        duration: int = AnimationDuration.SLOW,
    ) -> Optional[QSequentialAnimationGroup]:
        """Pulse a widget's opacity for feedback."""
        if cls.reduce_motion:
            return None

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        fade1 = QPropertyAnimation(effect, b"opacity")
        fade1.setDuration(duration // 2)
        fade1.setStartValue(1.0)
        fade1.setEndValue(0.4)
        fade1.setEasingCurve(AnimationEasing.FAST_OUT)

        fade2 = QPropertyAnimation(effect, b"opacity")
        fade2.setDuration(duration // 2)
        fade2.setStartValue(0.4)
        fade2.setEndValue(1.0)
        fade2.setEasingCurve(AnimationEasing.FAST_OUT)

        seq = QSequentialAnimationGroup()
        seq.addAnimation(fade1)
        seq.addAnimation(fade2)

        widget._active_pulse_group = seq  # type: ignore
        seq.start()
        return seq

    @classmethod
    def shake(cls, widget: QWidget) -> Optional[QSequentialAnimationGroup]:
        """Shake a widget horizontally for error feedback."""
        if cls.reduce_motion:
            return None

        pos = widget.pos()
        seq = QSequentialAnimationGroup()

        for delta in [8, -8, 5, -5, 2, -2, 0]:
            anim = QPropertyAnimation(widget, b"pos")
            anim.setDuration(35)
            anim.setEndValue(QPoint(pos.x() + delta, pos.y()))
            seq.addAnimation(anim)

        widget._active_shake_group = seq  # type: ignore
        seq.start()
        return seq
