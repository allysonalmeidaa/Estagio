import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QTextEdit, QGroupBox, QFormLayout, QSpinBox
)
from PyQt5.QtCore import Qt
from Transcricao_tab_V3 import TranscricaoTab
from Transcricao_conversão_tab_V3 import ConversaoTab

# Configuração e histórico padrão
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

        # Grupo Transcrição
        group_trans = QGroupBox("Configurações de Transcrição")
        form_trans = QFormLayout()
        self.combo_modelo = QComboBox()
        self.combo_modelo.addItems(["tiny", "base", "small", "medium", "large"])
        self.combo_modelo.setCurrentText(self.config.get("modelo", "small"))
        form_trans.addRow("Modelo Whisper:", self.combo_modelo)

        self.combo_idioma = QComboBox()
        for cod, nome in IDIOMAS:
            self.combo_idioma.addItem(nome, cod)
        idx_padrao = 0
        config_idioma = self.config.get("idioma", "auto")
        for i, (cod, nome) in enumerate(IDIOMAS):
            if cod == config_idioma:
                idx_padrao = i
                break
        self.combo_idioma.setCurrentIndex(idx_padrao)
        form_trans.addRow("Idioma padrão:", self.combo_idioma)

        self.spin_max_hist = QSpinBox()
        self.spin_max_hist.setRange(1, 100)
        self.spin_max_hist.setValue(self.config.get("max_historico", 20))
        form_trans.addRow("Máximo histórico:", self.spin_max_hist)
        group_trans.setLayout(form_trans)

        # Grupo Conversão
        group_conv = QGroupBox("Configurações de Conversão")
        form_conv = QFormLayout()
        self.input_dir_saida = QLineEdit(self.config.get("dir_saida_conversao", "saida_audio"))
        form_conv.addRow("Diretório de saída:", self.input_dir_saida)
        group_conv.setLayout(form_conv)

        # Botão Salvar
        btn_salvar = QPushButton("Salvar configurações")
        btn_salvar.clicked.connect(self.salvar)

        layout.addWidget(group_trans)
        layout.addWidget(group_conv)
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
        texto = """
        <b>Transcrição com Whisper (Qt)</b><br>
        Desenvolvido por Allyson Almeida Sirvano<br>
        Sob a supervisão de Mauricio Menon<br>
        Data: Junho/2025<br>
        <a href="https://github.com/allysonalmeidaa">GitHub do autor</a>
        """
        lbl = QLabel(texto)
        lbl.setTextFormat(Qt.RichText)
        lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
        lbl.setOpenExternalLinks(True)
        layout.addWidget(lbl)
        layout.addStretch()
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Processador de Áudio e Vídeo")
        self.setGeometry(200, 200, 900, 650)
        self.tabs = QTabWidget()
        self.tabs.addTab(TranscricaoTab(), "Transcrição")
        self.tabs.addTab(ConversaoTab(), "Conversão Multi-Formato")
        self.tabs.addTab(ConfigTab(), "Configurações")
        self.tabs.addTab(SobreTab(), "Sobre")
        self.setCentralWidget(self.tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())