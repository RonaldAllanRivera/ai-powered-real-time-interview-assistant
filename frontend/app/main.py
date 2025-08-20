import os
import sys
from pathlib import Path
from dotenv import load_dotenv

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

        self.btn_stop.setEnabled(False)
        self.btn_copy.setEnabled(False)

        top = QVBoxLayout()
        top.addWidget(QLabel("Live Transcript"))
        top.addWidget(self.transcript_view, 2)

        top.addWidget(QLabel("AI Suggested Answer"))
        top.addWidget(self.answer_view, 1)

        row = QHBoxLayout()
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_submit)
        row.addWidget(self.btn_copy)
        top.addLayout(row)
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

        # Backend client
        base_url = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
        self.backend = BackendClient(base_url) if BackendClient else None

        # Transcriber thread (lazy)
        self.transcriber = None

    # Stealth toggle removed

    def start_transcript(self):
        if TranscriberThread is None:
            QMessageBox.warning(self, "Missing deps", "Transcriber module not available. Install requirements.")
            return
        if self.transcriber and self.transcriber.isRunning():
            return
        self.transcriber = TranscriberThread()
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
        self.status_label.setText("Generating answer...")
        answer = None
        if self.backend:
            try:
                answer = self.backend.generate_answer(question, self.persona_id)
            except Exception as e:
                answer = None
        if not answer:
            answer = "[Backend not running yet] This is a placeholder answer."
        self.answer_view.setPlainText(answer)
        self.btn_copy.setEnabled(True)
        self.status_label.setText("Ready")

    def copy_answer(self):
        text = self.answer_view.toPlainText()
        QApplication.clipboard().setText(text)

    def closeEvent(self, event):
        """Ensure background threads are stopped cleanly on window close."""
        try:
            if self.transcriber and self.transcriber.isRunning():
                self.transcriber.stop()
                self.transcriber.wait(2000)
        except Exception:
            pass
        event.accept()


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
