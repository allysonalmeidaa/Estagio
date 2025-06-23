import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QIcon
from Transcricao_tab_V3 import TranscricaoTab
from Transcricao_conversão_tab_V3 import ConversaoTab

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PASTA_SCRIPT, "config.json")
IDIOMAS = [
    ("auto", "Detectar automático"),
    ("pt", "Português"),
    ("en", "Inglês"),
    ("es", "Espanhol"),
    ("fr", "Francês"),
    ("de", "Alemão"),
]

def carregar_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

class ConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config = carregar_config()
        layout = QVBoxLayout()
        form = QFormLayout()
        self.combo_modelo = QComboBox()
        self.combo_modelo.addItems(["tiny", "base", "small", "medium", "large"])
        self.combo_modelo.setCurrentText(self.config.get("modelo", "small"))
        form.addRow("Modelo Whisper:", self.combo_modelo)
        self.combo_idioma = QComboBox()
        for cod, nome in IDIOMAS:
            self.combo_idioma.addItem(nome, cod)
        idx = [i for i, (cod, _) in enumerate(IDIOMAS) if cod == self.config.get("idioma", "auto")]
        self.combo_idioma.setCurrentIndex(idx[0] if idx else 0)
        form.addRow("Idioma padrão:", self.combo_idioma)
        self.spin_max_hist = QSpinBox()
        self.spin_max_hist.setRange(1, 100)
        self.spin_max_hist.setValue(self.config.get("max_historico", 20))
        form.addRow("Máximo histórico:", self.spin_max_hist)
        # Conversão
        self.input_dir_saida = QLineEdit(self.config.get("dir_saida_conversao", "saida_audio"))
        form.addRow("Pasta saída conversão:", self.input_dir_saida)
        btn_salvar = QPushButton("Salvar configurações")
        btn_salvar.clicked.connect(self.salvar)
        layout.addLayout(form)
        layout.addWidget(btn_salvar)
        layout.addStretch()
        self.setLayout(layout)
    def salvar(self):
        novo_config = carregar_config()
        novo_config["modelo"] = self.combo_modelo.currentText()
        novo_config["idioma"] = self.combo_idioma.currentData()
        novo_config["max_historico"] = self.spin_max_hist.value()
        novo_config["dir_saida_conversao"] = self.input_dir_saida.text().strip() or "saida_audio"
        salvar_config(novo_config)
        self.config = novo_config
        QMessageBox.information(self, "Configurações", "Configurações salvas com sucesso!")

class SobreTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        lbl = QLabel(
            "<b>Transcrição com Whisper (Qt)</b><br>"
            "Desenvolvido por Allyson Almeida Sirvano<br>"
            "Sob a supervisão de Mauricio Menon<br>"
            "Data: Junho/2025<br>"
            "<a href='https://github.com/allysonalmeidaa'>GitHub do autor</a>"
        )
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        lbl.setOpenExternalLinks(True)
        layout.addWidget(lbl)
        layout.addStretch()
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcrição com Whisper (Qt)")
        # Ícone do aplicativo
        icon_path = os.path.join(os.path.dirname(__file__), "microphone2.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(200, 200, 1200, 700)
        self.tabs = QTabWidget()
        self.tabs.addTab(TranscricaoTab(), "Transcrição")
        self.tabs.addTab(ConversaoTab(), "Conversão")
        self.tabs.addTab(ConfigTab(), "Configurações")
        self.tabs.addTab(SobreTab(), "Sobre")
        self.setCentralWidget(self.tabs)

def set_basic_palette(app):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f5f5f5"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#222"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#fff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f2f2f2"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#222"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#f2f2f2"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#222"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 0))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#fff"))
    app.setPalette(palette)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_basic_palette(app)
    app.setStyleSheet("""
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
            background: #f5f5f5;
        }
        QTabWidget::pane {
            border: 1px solid #bbbbbb;
            border-radius: 5px;
            background: #f8f8f8;
        }
        QTabBar::tab {
            background: #eaeaea;
            border: 1px solid #bbbbbb;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            min-width: 130px;
            min-height: 32px;
            margin: 0 2px 0 0;
            padding: 4px 18px;
        }
        QTabBar::tab:selected {
            background: #fff;
            color: #207d20;
            border-bottom: 2px solid #207d20;
            font-weight: 500;
        }
        QTabBar::tab:!selected {
            color: #444;
        }
        QLabel { color: #222; }
        QLineEdit, QTextEdit, QComboBox, QListWidget, QSpinBox {
            background: #fff;
            color: #222;
            border: 1px solid #bbb;
            border-radius: 4px;
            padding: 5px;
            selection-background-color: #207d20;
            selection-color: white;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QListWidget:focus, QSpinBox:focus {
            border: 1.5px solid #207d20;
            background: #f8fff8;
        }
        QPushButton {
            background-color: #eaeaea;
            color: #222;
            border: 1px solid #bbbbbb;
            border-radius: 4px;
            padding: 7px 25px;
            font-weight: 500;
            min-width: 170px;
        }
        QPushButton:pressed { background-color: #b9e2b9; }
        QPushButton:hover { background-color: #e0ffe0; color: #207d20; }
        QProgressBar {
            border: 1px solid #bbb;
            border-radius: 4px;
            text-align: center;
            background: #f3f6fa;
            height: 16px;
        }
        QProgressBar::chunk {
            background-color: #207d20;
            width: 16px;
        }
        QListWidget {
            border: 1px solid #bbb;
            border-radius: 4px;
        }
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())