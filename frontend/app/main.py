import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import hashlib

from PySide6.QtCore import Qt, QThread, Signal
 # (Tray icon removed)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QComboBox,
    QLineEdit,
    QFormLayout,
    QToolButton,
    QStyle,
    QCheckBox,
)

# Lazy import of services to avoid hard dependency at start
try:
    from .services.transcriber import TranscriberThread
except Exception:
    TranscriberThread = None  # type: ignore

try:
    from .services.backend_client import BackendClient
except Exception:
    BackendClient = None  # type: ignore


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Interview Assistant")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.95)
        self.resize(520, 600)

        # State
        self.session_id = None
        self.persona_id = None
        self.personas = []
        self.model_id = None
        self.models = []
        self.last_prompt_hash = None
        # Stealth mode removed

        # UI
        self.transcript_view = QTextEdit()
        self.transcript_view.setReadOnly(True)
        self.answer_view = QTextEdit()

        self.status_label = QLabel("Idle")

        self.btn_start = QPushButton("Start Transcript")
        self.btn_stop = QPushButton("Stop Transcript")
        self.btn_submit = QPushButton("Submit → Generate Answer")
        self.btn_copy = QPushButton("Copy Answer")
        self.btn_save_info = QPushButton("Save Info")
        self.btn_reset = QPushButton("Reset Transcript")
        self.chk_clear_after = QCheckBox("Clear after answer")
        self.chk_clear_after.setChecked(True)

        # Interview metadata inputs
        self.persona_combo = QComboBox()
        self.model_combo = QComboBox()
        # Audio device selection
        self.device_combo = QComboBox()
        self.btn_refresh_devices = QToolButton()
        self.btn_refresh_devices.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_refresh_devices.setToolTip("Refresh audio devices (WASAPI loopback)")
        self.input_company = QLineEdit()
        self.input_role = QLineEdit()
        self.input_context = QTextEdit()
        self.input_company.setPlaceholderText("e.g., ACME Corp")
        self.input_role.setPlaceholderText("e.g., Senior Backend Engineer")
        self.input_context.setPlaceholderText("Paste job description or notes…")

        # Interview Notes soft limit + live counter
        try:
            self.context_limit = int(os.getenv("INTERVIEW_NOTES_SOFT_LIMIT", "10000"))
        except Exception:
            self.context_limit = 10000
        self.context_counter = QLabel(f"0 / {self.context_limit:,}")
        self.context_counter.setToolTip(
            "Soft limit for Interview Notes. If exceeded, the backend will include a truncated head/tail for performance."
        )
        self.input_context.textChanged.connect(self.update_context_counter)

        self.btn_stop.setEnabled(False)
        self.btn_copy.setEnabled(False)

        top = QVBoxLayout()
        form = QFormLayout()
        # Help icon for personas
        self.persona_help = QToolButton()
        self.persona_help.setIcon(self.style().standardIcon(QStyle.SP_DialogHelpButton))
        self.persona_help.setToolTip("What do these personas do?")
        self.persona_help.setAutoRaise(True)

        persona_label_widget = QWidget()
        persona_label_layout = QHBoxLayout()
        persona_label_layout.setContentsMargins(0, 0, 0, 0)
        persona_label_layout.addWidget(QLabel("Persona"))
        persona_label_layout.addWidget(self.persona_help)
        persona_label_layout.addStretch()
        persona_label_widget.setLayout(persona_label_layout)

        form.addRow(persona_label_widget, self.persona_combo)

        # Help icon for model selection
        self.model_help = QToolButton()
        self.model_help.setIcon(self.style().standardIcon(QStyle.SP_DialogHelpButton))
        self.model_help.setToolTip("Which model should I use?")
        self.model_help.setAutoRaise(True)

        model_label_widget = QWidget()
        model_label_layout = QHBoxLayout()
        model_label_layout.setContentsMargins(0, 0, 0, 0)
        model_label_layout.addWidget(QLabel("Model"))
        model_label_layout.addWidget(self.model_help)
        model_label_layout.addStretch()
        model_label_widget.setLayout(model_label_layout)

        form.addRow(model_label_widget, self.model_combo)
        # Device row with refresh tool button
        device_row_widget = QWidget()
        device_row_layout = QHBoxLayout()
        device_row_layout.setContentsMargins(0, 0, 0, 0)
        device_row_layout.addWidget(self.device_combo)
        device_row_layout.addWidget(self.btn_refresh_devices)
        device_row_widget.setLayout(device_row_layout)
        form.addRow("Capture Device", device_row_widget)
        form.addRow("Company", self.input_company)
        form.addRow("Role", self.input_role)
        form.addRow("Interview Notes", self.input_context)
        form.addRow("", self.context_counter)
        top.addLayout(form)
        top.addWidget(self.btn_save_info)
        top.addWidget(QLabel("Live Transcript"))
        top.addWidget(self.transcript_view, 2)

        top.addWidget(QLabel("AI Suggested Answer"))
        top.addWidget(self.answer_view, 1)

        row = QHBoxLayout()
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_submit)
        row.addWidget(self.btn_copy)
        row.addWidget(self.btn_reset)
        top.addLayout(row)
        top.addWidget(self.chk_clear_after)
        top.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(top)
        self.setCentralWidget(container)

        # Tray removed

        # Events
        self.btn_start.clicked.connect(self.start_transcript)
        self.btn_stop.clicked.connect(self.stop_transcript)
        self.btn_submit.clicked.connect(self.submit_for_answer)
        self.btn_copy.clicked.connect(self.copy_answer)
        self.btn_save_info.clicked.connect(self.save_interview_info)
        self.btn_reset.clicked.connect(self.reset_transcript)
        self.persona_combo.currentIndexChanged.connect(self.on_persona_changed)
        self.persona_help.clicked.connect(self.show_persona_help)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        self.model_help.clicked.connect(self.show_model_help)
        self.btn_refresh_devices.clicked.connect(self.refresh_devices)

        # Backend client
        base_url = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
        self.backend = BackendClient(base_url) if BackendClient else None

        # Transcriber thread (lazy)
        self.transcriber = None

        # Load models, personas and interview info
        self.load_models()
        self.load_initial_data()
        # initialize counter after initial data load
        self.update_context_counter()
        # populate audio devices
        self.refresh_devices()

    # Stealth toggle removed

    def start_transcript(self):
        if TranscriberThread is None:
            QMessageBox.warning(self, "Missing deps", "Transcriber module not available. Install requirements.")
            return
        if self.transcriber and self.transcriber.isRunning():
            return
        device_name = None
        try:
            device_name = (self.device_combo.currentText() or "").strip() or None
        except Exception:
            device_name = None
        self.transcriber = TranscriberThread(device_name=device_name)
        self.transcriber.transcriptReady.connect(self.on_transcript)
        self.transcriber.started.connect(lambda: self.status_label.setText("Transcribing..."))
        self.transcriber.finished.connect(lambda: self.status_label.setText("Stopped"))
        self.transcriber.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def stop_transcript(self):
        if self.transcriber and self.transcriber.isRunning():
            self.transcriber.stop()
            self.transcriber.wait(2000)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def on_transcript(self, text: str):
        if not text:
            return
        self.transcript_view.append(text)
        # Any new text invalidates the last submitted hash
        self.last_prompt_hash = None
        # Optionally post to backend for persistence
        if self.backend:
            try:
                self.backend.post_transcript(text)
            except Exception:
                pass

    def submit_for_answer(self):
        question = self.transcript_view.toPlainText().strip()
        if not question:
            QMessageBox.information(self, "No transcript", "Nothing to submit yet.")
            return
        # Dedupe: avoid answering the exact same transcript content again
        try:
            h = hashlib.sha256(question.encode("utf-8")).hexdigest()
        except Exception:
            h = None
        if self.last_prompt_hash and h and h == self.last_prompt_hash:
            QMessageBox.information(self, "Already answered", "This transcript was already answered. Add new content or Reset.")
            return
        self.status_label.setText("Generating answer...")
        answer = None
        if self.backend:
            try:
                answer = self.backend.generate_answer(question, self.persona_id, self.model_id)
            except Exception as e:
                answer = None
        if not answer:
            answer = "[Backend not running yet] This is a placeholder answer."
        self.answer_view.setPlainText(answer)
        self.btn_copy.setEnabled(True)
        # Remember the last answered prompt hash
        self.last_prompt_hash = h
        # Auto-clear transcript if enabled
        if self.chk_clear_after.isChecked():
            self.reset_transcript()
        self.status_label.setText("Ready")

    def copy_answer(self):
        text = self.answer_view.toPlainText()
        QApplication.clipboard().setText(text)

    def reset_transcript(self):
        """Clear the live transcript UI only and reset dedupe state."""
        try:
            self.transcript_view.clear()
            self.last_prompt_hash = None
            self.status_label.setText("Transcript cleared")
        except Exception:
            pass

    def update_context_counter(self):
        """Update the Interview Notes character counter and warn when exceeding soft limit."""
        try:
            n = len(self.input_context.toPlainText())
            self.context_counter.setText(f"{n:,} / {self.context_limit:,}")
            if n > self.context_limit:
                # Warn color
                self.context_counter.setStyleSheet("color: #b00020;")
                self.context_counter.setToolTip(
                    "Interview Notes exceed the soft limit; backend will truncate head/tail for speed."
                )
            else:
                self.context_counter.setStyleSheet("")
                self.context_counter.setToolTip(
                    "Soft limit for Interview Notes. If exceeded, the backend will include a truncated head/tail for performance."
                )
        except Exception:
            pass

    def on_persona_changed(self, idx: int):
        try:
            data = self.persona_combo.currentData()
            if isinstance(data, dict):
                self.persona_id = data.get("id")
            else:
                self.persona_id = data
        except Exception:
            self.persona_id = None

    def save_interview_info(self):
        company = self.input_company.text().strip()
        role = self.input_role.text().strip()
        context = self.input_context.toPlainText().strip()
        ok = False
        if self.backend:
            try:
                ok = self.backend.upsert_interview_info(company or None, role or None, context or None)
            except Exception:
                ok = False
        self.status_label.setText("Info saved" if ok else "Save failed")

    def load_initial_data(self):
        if not self.backend:
            return
        # Personas
        try:
            personas = self.backend.get_personas() or []
            self.personas = personas
            self.persona_combo.clear()
            for p in personas:
                self.persona_combo.addItem(p.get("name", ""), p)
                idx = self.persona_combo.count() - 1
                tooltip = (p.get("description") or "").strip()
                if tooltip:
                    self.persona_combo.setItemData(idx, tooltip, Qt.ToolTipRole)
            if personas:
                self.persona_combo.setCurrentIndex(0)
                data = self.persona_combo.currentData()
                self.persona_id = data.get("id") if isinstance(data, dict) else data
        except Exception:
            pass
        # Interview info
        try:
            info = self.backend.get_interview_info()
            if info:
                self.input_company.setText(info.get("company", "") or "")
                self.input_role.setText(info.get("role", "") or "")
                self.input_context.setPlainText(info.get("context", "") or "")
        except Exception:
            pass
    def closeEvent(self, event):
        """Ensure background threads are stopped cleanly on window close."""
        try:
            if self.transcriber and self.transcriber.isRunning():
                self.transcriber.stop()
                self.transcriber.wait(2000)
        except Exception:
            pass
        event.accept()

    def refresh_devices(self):
        """Enumerate WASAPI loopback devices and populate the combo box.
        Falls back gracefully if dependencies are missing.
        """
        try:
            # Import here to avoid hard dependency at startup
            import soundcard as sc  # type: ignore
        except Exception:
            # No deps -> keep simulation-only label
            self.device_combo.clear()
            self.device_combo.addItem("Simulated (no audio deps)")
            return
        try:
            mics = sc.all_microphones(include_loopback=True)
            self.device_combo.clear()
            for m in mics:
                self.device_combo.addItem(m.name)
            if not mics:
                self.device_combo.addItem("No loopback devices found")
        except Exception:
            self.device_combo.clear()
            self.device_combo.addItem("Device enumeration error")

    def show_persona_help(self):
        """Show details about the currently selected persona, including description and the AI prompt used."""
        try:
            data = self.persona_combo.currentData()
            if isinstance(data, dict):
                name = data.get("name", "Persona")
                desc = (data.get("description") or "").strip()
                prompt = (data.get("system_prompt") or "").strip()
            else:
                name = self.persona_combo.currentText()
                desc = "Select a persona to view details."
                prompt = ""

            parts = []
            parts.append(f"<b>{name}</b>")
            if desc:
                parts.append(desc.replace("\n", "<br>"))
            if prompt:
                parts.append("<b>Prompt used by AI:</b>")
                # Use <pre> for readability; kept simple to avoid heavy formatting
                parts.append(f"<pre style='white-space:pre-wrap'>{prompt}</pre>")
            html = "<br><br>".join(parts)
            QMessageBox.information(self, "Persona help", html)
        except Exception:
            QMessageBox.information(self, "Persona help", "Select a persona to view details.")

    def load_models(self):
        """Populate model selector with fast defaults and tooltips."""
        try:
            self.models = [
                {
                    "id": "gpt-4o-mini",
                    "name": "gpt-4o-mini (fast)",
                    "tooltip": "Fastest + low cost. Great for live interviews. Slightly less depth vs gpt-4o.",
                    "pros": ["Lowest latency", "Lower cost"],
                    "cons": ["Less nuanced than gpt-4o"],
                },
                {
                    "id": "gpt-4o",
                    "name": "gpt-4o (higher quality)",
                    "tooltip": "Higher quality/reasoning. Slower and higher cost vs 4o-mini.",
                    "pros": ["Best quality in 4o family"],
                    "cons": ["Higher latency", "Higher cost"],
                },
            ]
            self.model_combo.clear()
            for m in self.models:
                self.model_combo.addItem(m["name"], m)
                idx = self.model_combo.count() - 1
                self.model_combo.setItemData(idx, m.get("tooltip", ""), Qt.ToolTipRole)
            if self.models:
                # Default to speed-first
                self.model_combo.setCurrentIndex(0)
                cur = self.model_combo.currentData()
                self.model_id = cur.get("id") if isinstance(cur, dict) else cur
        except Exception:
            self.model_id = "gpt-4o-mini"

    def on_model_changed(self, idx: int):
        try:
            data = self.model_combo.currentData()
            if isinstance(data, dict):
                self.model_id = data.get("id")
            else:
                self.model_id = data
        except Exception:
            self.model_id = None

    def show_model_help(self):
        try:
            parts = ["<b>Model options</b>"]
            for m in self.models:
                pros = "<br>".join([f"+ {p}" for p in m.get("pros", [])])
                cons = "<br>".join([f"- {c}" for c in m.get("cons", [])])
                parts.append(f"<b>{m['name']}</b><br>{m.get('tooltip','')}<br>{pros}<br>{cons}")
            html = "<br><br>".join(parts)
            QMessageBox.information(self, "Model help", html)
        except Exception:
            QMessageBox.information(self, "Model help", "Choose gpt-4o-mini for speed; gpt-4o for quality.")


def main():
    # Load .env from frontend folder
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
