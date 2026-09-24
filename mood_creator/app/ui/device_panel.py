from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.windows.audio import AudioManager
from app.windows.devices import DeviceManager


class DeviceScanWorker(QThread):
    """Background worker to query audio and MIDI devices without freezing UI."""
    devices_scanned = Signal(list, list)  # audio_devs, midi_devs

    def __init__(self, dev_manager: DeviceManager, parent=None):
        super().__init__(parent)
        self.dev_manager = dev_manager

    def run(self) -> None:
        audio_devs = self.dev_manager.get_audio_devices("all")
        midi_devs = self.dev_manager.get_midi_devices()
        self.devices_scanned.emit(audio_devs, midi_devs)


class DevicePanelView(QWidget):
    """View inspecting hardware peripherals (Audio interfaces, MIDI devices)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dev_manager = DeviceManager()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title_lbl = QLabel("Hardware & Peripherals")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;")

        self.refresh_btn = QPushButton("🔄 Refresh Devices")
        self.refresh_btn.setProperty("class", "SecondaryButton")
        self.refresh_btn.clicked.connect(self.refresh_devices)

        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(header_layout)

        # Audio Devices Section Header & Quick Action Buttons
        audio_bar = QHBoxLayout()
        audio_lbl = QLabel("Audio Endpoints (Inputs & Outputs)")
        audio_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        
        self.set_def_out_btn = QPushButton("Set Default Output")
        self.set_def_out_btn.setProperty("class", "SecondaryButton")
        self.set_def_out_btn.clicked.connect(self._set_selected_default_output)

        self.set_def_in_btn = QPushButton("Set Default Input")
        self.set_def_in_btn.setProperty("class", "SecondaryButton")
        self.set_def_in_btn.clicked.connect(self._set_selected_default_input)

        audio_bar.addWidget(audio_lbl)
        audio_bar.addStretch()
        audio_bar.addWidget(self.set_def_out_btn)
        audio_bar.addWidget(self.set_def_in_btn)

        main_layout.addLayout(audio_bar)

        # Audio Table
        self.audio_table = QTableWidget(0, 4)
        self.audio_table.setHorizontalHeaderLabels(["Device Name", "Type", "Status", "Default Endpoint"])
        self.audio_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.audio_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.audio_table)

        # MIDI Devices Section Header
        midi_lbl = QLabel("MIDI Keyboards & Controllers")
        midi_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8; margin-top: 12px;")
        main_layout.addWidget(midi_lbl)

        # MIDI Table
        self.midi_table = QTableWidget(0, 3)
        self.midi_table.setHorizontalHeaderLabels(["Device Name", "Port Type", "Status"])
        self.midi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.midi_table)

        self.refresh_devices()

    def refresh_devices(self) -> None:
        """Query system for audio and MIDI hardware in background thread."""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳ Scanning...")

        self.worker = DeviceScanWorker(self.dev_manager, parent=self)
        self.worker.devices_scanned.connect(self._on_devices_scanned)
        self.worker.start()

    def _on_devices_scanned(self, audio_devs: list, midi_devs: list) -> None:
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 Refresh Devices")

        # 1. Audio Devices
        self.audio_table.setRowCount(len(audio_devs))
        for row, dev in enumerate(audio_devs):
            self.audio_table.setItem(row, 0, QTableWidgetItem(dev.name))
            self.audio_table.setItem(row, 1, QTableWidgetItem(dev.device_type.upper()))
            
            status_item = QTableWidgetItem("● Connected" if dev.is_connected else "○ Offline")
            status_item.setForeground(Qt.GlobalColor.green if dev.is_connected else Qt.GlobalColor.red)
            self.audio_table.setItem(row, 2, status_item)

            def_item = QTableWidgetItem("✓ Default" if dev.is_default else "")
            self.audio_table.setItem(row, 3, def_item)

        # 2. MIDI Devices
        self.midi_table.setRowCount(len(midi_devs))
        for row, dev in enumerate(midi_devs):
            self.midi_table.setItem(row, 0, QTableWidgetItem(dev.name))
            self.midi_table.setItem(row, 1, QTableWidgetItem(dev.device_type.upper()))

            status_item = QTableWidgetItem("● Connected" if dev.is_connected else "○ Offline")
            status_item.setForeground(Qt.GlobalColor.green if dev.is_connected else Qt.GlobalColor.red)
            self.midi_table.setItem(row, 2, status_item)

    def _set_selected_default_output(self) -> None:
        row = self.audio_table.currentRow()
        if row >= 0:
            dev_name = self.audio_table.item(row, 0).text()
            ok = AudioManager.set_default_device(dev_name, device_type="output")
            if ok:
                QMessageBox.information(self, "Audio Configured", f"Set default output device to '{dev_name}'.")
                self.refresh_devices()

    def _set_selected_default_input(self) -> None:
        row = self.audio_table.currentRow()
        if row >= 0:
            dev_name = self.audio_table.item(row, 0).text()
            ok = AudioManager.set_default_device(dev_name, device_type="input")
            if ok:
                QMessageBox.information(self, "Audio Configured", f"Set default input device to '{dev_name}'.")
                self.refresh_devices()
