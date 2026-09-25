"""World-class Mode Card component matching the reference design.

Features atmospheric background photography, gradient fade mask, tactile hover glow,
hotkey pill badge, and bottom-right circular execution arrow.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Property, QEasingCurve, QPoint, QPropertyAnimation, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.mode import Mode
from app.ui.animation_manager import AnimationManager
from app.ui.styles.design_tokens import AnimationDuration, DarkPalette


class ModeCard(QFrame):
    """Interactive Mode Card with artwork background, gradient mask, and execution trigger."""

    run_requested = Signal(str)        # mode_id
    edit_requested = Signal(str)       # mode_id
    export_requested = Signal(str)     # mode_id
    duplicate_requested = Signal(str)  # mode_id
    delete_requested = Signal(str)     # mode_id

    # Mapping mode ID keywords to background assets
    ARTWORK_MAP = {
        "guitar": "mode_guitar.jpg",
        "gaming": "mode_gaming.jpg",
        "coding": "mode_coding.jpg",
        "music": "mode_music.jpg",
        "study": "mode_study.jpg",
        "movie": "mode_movie.jpg",
    }

    def __init__(self, mode: Mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setObjectName("ModeCard")
        self.setMinimumWidth(240)
        self.setMaximumWidth(340)
        self.setFixedHeight(185)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_hovered = False
        self._hover_progress: float = 0.0
        self._hover_anim = QPropertyAnimation(self, b"hover_progress", self)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Load background artwork if available
        self.bg_pixmap: Optional[QPixmap] = None
        self._load_artwork()

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(6)

        # 1. Top row: Icon Badge
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        from app.services.icon_service import IconService
        app_pix = IconService.get_instance().get_mode_app_icon(mode, size=24)

        self.icon_badge = QLabel()
        self.icon_badge.setFixedSize(38, 38)
        self.icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if app_pix and not app_pix.isNull():
            self.icon_badge.setPixmap(app_pix)
            self.icon_badge.setStyleSheet(
                """
                QLabel {
                    background-color: rgba(18, 22, 34, 0.85);
                    border: 1px solid rgba(56, 189, 248, 0.4);
                    border-radius: 19px;
                    padding: 3px;
                }
                """
            )
        else:
            self.icon_badge.setText(self._get_display_icon())
            self.icon_badge.setStyleSheet(
                """
                QLabel {
                    background-color: rgba(18, 22, 34, 0.85);
                    border: 1px solid rgba(40, 48, 70, 0.9);
                    border-radius: 19px;
                    font-size: 16px;
                    color: #ffffff;
                }
                """
            )
        top_layout.addWidget(self.icon_badge)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # 2. Mode Title
        self.title_lbl = QLabel(self._clean_title(mode.name))
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff; background: transparent;")
        main_layout.addWidget(self.title_lbl)

        # 3. Description
        self.desc_lbl = QLabel(mode.description)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.3; background: transparent;")
        self.desc_lbl.setMaximumHeight(36)
        main_layout.addWidget(self.desc_lbl)

        main_layout.addStretch()

        # 4. Bottom Row: Hotkey Badge (left) & Run Arrow Button (right)
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        hotkey_text = self._format_hotkey(mode.hotkey)
        self.hotkey_badge = QLabel(hotkey_text)
        self.hotkey_badge.setStyleSheet(
            """
            QLabel {
                background-color: rgba(15, 18, 28, 0.8);
                color: #cbd5e1;
                border: 1px solid rgba(40, 46, 66, 0.8);
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: 600;
            }
            """
        )
        bottom_layout.addWidget(self.hotkey_badge)
        bottom_layout.addStretch()

        # Circular Run Arrow Button
        self.run_btn = QPushButton("›")
        self.run_btn.setFixedSize(30, 30)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setToolTip(f"Launch {mode.name}")
        self.run_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(22, 26, 40, 0.85);
                color: #f8fafc;
                border: 1px solid rgba(45, 55, 80, 0.8);
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #0284c7;
                border-color: #38bdf8;
                color: #ffffff;
            }
            """
        )
        self.run_btn.clicked.connect(lambda: self.run_requested.emit(self.mode.id))
        bottom_layout.addWidget(self.run_btn)

        main_layout.addLayout(bottom_layout)

    @Property(float)
    def hover_progress(self) -> float:
        return self._hover_progress

    @hover_progress.setter
    def hover_progress(self, val: float) -> None:
        self._hover_progress = val
        self.update()

    def _clean_title(self, name: str) -> str:
        """Strip 'Mode' from name cleanly (e.g. 'Guitar', 'Gaming', 'Valo')."""
        import re
        clean = re.sub(r"\s+mode$", "", name, flags=re.IGNORECASE).strip()
        return clean or name

    def _get_display_icon(self) -> str:
        m_id = self.mode.id.lower()
        if "guitar" in m_id:
            return "🎸"
        elif "gaming" in m_id:
            return "🎮"
        elif "coding" in m_id:
            return "</>"
        elif "music" in m_id:
            return "🎵"
        elif "study" in m_id:
            return "📖"
        elif "movie" in m_id:
            return "🎬"
        return self.mode.icon or "⚡"

    def _format_hotkey(self, hotkey: Optional[str]) -> str:
        if not hotkey:
            return "⌘ ·"
        hk = hotkey.upper().replace("CTRL+ALT+", "⌘ ").replace("CTRL+", "⌘ ").replace("ALT+", "⌥ ")
        return hk

    def _load_artwork(self) -> None:
        m_id = self.mode.id.lower()
        filename = None
        for key, fname in self.ARTWORK_MAP.items():
            if key in m_id:
                filename = fname
                break

        if filename:
            app_dir = Path(__file__).resolve().parent.parent.parent.parent
            art_path = app_dir / "assets" / "ui" / filename
            if art_path.exists():
                pix = QPixmap(str(art_path))
                if not pix.isNull():
                    self.bg_pixmap = pix

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        # Rounded card path
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 16, 16)
        painter.setClipPath(path)

        # Base background fill
        painter.fillPath(path, QBrush(QColor("#08090e")))

        # Draw right-aligned artwork if present
        if getattr(self, "bg_pixmap", None) is not None and not self.bg_pixmap.isNull():
            art_w = int(w * 0.58)
            art_rect = QRect(w - art_w, 0, art_w, h)
            scaled_pix = self.bg_pixmap.scaled(
                art_w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(art_rect, scaled_pix)

            # Gradient mask over artwork to fade leftwards into #08090e
            grad = QLinearGradient(w - art_w - 10, 0, w, 0)
            grad.setColorAt(0.0, QColor(8, 9, 14, 255))
            grad.setColorAt(0.45, QColor(8, 9, 14, 220))
            grad.setColorAt(0.85, QColor(8, 9, 14, 90))
            grad.setColorAt(1.0, QColor(8, 9, 14, 40))

            painter.fillRect(rect, QBrush(grad))

        # Card Border (Smooth liquid hover interpolation from #181b26 to #38bdf8)
        painter.setClipping(False)
        p = self._hover_progress
        r = int(24 + (56 - 24) * p)
        g = int(27 + (189 - 27) * p)
        b = int(38 + (248 - 38) * p)
        border_pen = QPen(QColor(r, g, b), 1.0 + 0.5 * p)

        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 16, 16)

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self._is_hovered = True
        self._hover_anim.stop()
        self._hover_anim.setDuration(120)
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._is_hovered = False
        self._hover_anim.stop()
        self._hover_anim.setDuration(150)
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            # Clicking anywhere on the card triggers the mode run
            self.run_requested.emit(self.mode.id)
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu()

    def _show_context_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #0b0d14;
                color: #f8fafc;
                border: 1px solid #1e2434;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1e293b;
                color: #38bdf8;
            }
            """
        )
        edit_action = menu.addAction("✏️  Edit Mode")
        dup_action = menu.addAction("📋  Duplicate Mode")
        exp_action = menu.addAction("📤  Export JSON")
        menu.addSeparator()
        del_action = menu.addAction("🗑  Delete Mode")

        action = menu.exec(self.cursor().pos())
        if action == edit_action:
            self.edit_requested.emit(self.mode.id)
        elif action == dup_action:
            self.duplicate_requested.emit(self.mode.id)
        elif action == exp_action:
            self.export_requested.emit(self.mode.id)
        elif action == del_action:
            self.delete_requested.emit(self.mode.id)
