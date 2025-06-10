import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QFileDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox, QMessageBox, QProgressBar, QListWidget, QLineEdit, QDialog
)
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from transcricao_core import transcrever_com_diarizacao

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
HISTORICO_PATH = os.path.join(PASTA_SCRIPT, "historico.json")
CONFIG_PATH = os.path.join(PASTA_SCRIPT, "config.json")

IDIOMAS = [
    ("auto", "Detectar automático"),
    ("pt", "Português"),
    ("en", "Inglês"),
    ("es", "Espanhol"),
    ("fr", "Francês"),
    ("de", "Alemão"),
    # Adicione outros idiomas se desejar
]

class DropWidget(QWidget):
    fileDropped = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.flac')):
                self.fileDropped.emit(file_path)
                break

class ConfigDialog(QDialog):
    def __init__(self, config_atual):
        super().__init__()
        self.setWindowTitle("Configurações")
        self.setFixedSize(320, 200)

        self.combo_modelo = QComboBox()
        self.combo_modelo.addItems(["tiny", "base", "small", "medium", "large"])
        self.combo_modelo.setCurrentText(config_atual.get("modelo", "small"))

        self.combo_idioma = QComboBox()
        for cod, nome in IDIOMAS:
            self.combo_idioma.addItem(nome, cod)
        idx_padrao = 0
        config_idioma = config_atual.get("idioma", "auto")
        for i, (cod, nome) in enumerate(IDIOMAS):
            if cod == config_idioma:
                idx_padrao = i
                break
        self.combo_idioma.setCurrentIndex(idx_padrao)

        self.txt_max_hist = QLineEdit(str(config_atual.get("max_historico", 20)))
        self.txt_max_hist.setValidator(QIntValidator(1, 100))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Modelo padrão:"))
        layout.addWidget(self.combo_modelo)
        layout.addWidget(QLabel("Idioma padrão:"))
        layout.addWidget(self.combo_idioma)
        layout.addWidget(QLabel("Máximo de itens no histórico:"))
        layout.addWidget(self.txt_max_hist)

        btns = QHBoxLayout()
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self.accept)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_salvar)
        btns.addWidget(btn_cancelar)
        layout.addLayout(btns)

        self.setLayout(layout)

    def get_config(self):
        return {
            "modelo": self.combo_modelo.currentText(),
            "idioma": self.combo_idioma.currentData(),
            "max_historico": int(self.txt_max_hist.text() or 20)
        }

class TranscricaoThread(QThread):
    progresso = pyqtSignal(int, str)
    resultado = pyqtSignal(str)
    erro = pyqtSignal(str)
    def __init__(self, caminho, modelo, idioma):
        super().__init__()
        self.caminho = caminho
        self.modelo = modelo
        self.idioma = idioma
    def run(self):
        try:
            def progresso_callback(valor, texto=""):
                self.progresso.emit(valor, texto)
            texto = transcrever_com_diarizacao(self.caminho, self.modelo, self.idioma, progresso_callback)
            self.resultado.emit(texto)
        except Exception as e:
            self.erro.emit(str(e))

class TranscricaoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        icon_path = os.path.join(os.path.dirname(__file__), "microphone2.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Transcrição com Whisper (Qt)")
        self.setGeometry(200, 200, 900, 650)

        self.config = self.carregar_config()

        self.caminho_arquivo = ""
        self.label_arquivo = QLabel("Arquivo: nenhum selecionado")

        self.label_status = QLabel("Aguardando para começar.")

        self.btn_abrir = QPushButton("Selecionar arquivo")
        self.btn_abrir.clicked.connect(self.selecionar_arquivo)

        self.btn_config = QPushButton("Configurações")
        self.btn_config.clicked.connect(self.abrir_configuracoes)

        self.label_modelo = QLabel("Modelo Whisper:")
        self.combo_modelos = QComboBox()
        self.combo_modelos.addItems(["tiny", "base", "small", "medium", "large"])
        self.combo_modelos.setCurrentText(self.config.get("modelo", "small"))

        self.label_idioma = QLabel("Idioma:")
        self.combo_idioma = QComboBox()
        for cod, nome in IDIOMAS:
            self.combo_idioma.addItem(nome, cod)
        idx_idioma = 0
        config_idioma = self.config.get("idioma", "auto")
        for i, (cod, nome) in enumerate(IDIOMAS):
            if cod == config_idioma:
                idx_idioma = i
                break
        self.combo_idioma.setCurrentIndex(idx_idioma)

        self.btn_transcrever = QPushButton("Transcrever")
        self.btn_transcrever.clicked.connect(self.transcrever)

        self.texto_transcricao = QTextEdit()
        self.texto_transcricao.setReadOnly(True)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setVisible(False)

        self.drop_area = DropWidget()
        self.drop_area.setMinimumHeight(60)
        self.drop_area.setStyleSheet("border: 2px dashed #aaa; background: #f3f3f3;")
        self.drop_area.fileDropped.connect(self.arquivo_arrastado)
        self.drop_label = QLabel("Arraste e solte um arquivo de áudio ou vídeo aqui")
        self.drop_label.setAlignment(Qt.AlignCenter)

        self.busca_historico = QLineEdit()
        self.busca_historico.setPlaceholderText("Buscar no histórico...")
        self.busca_historico.textChanged.connect(self.filtrar_historico)

        self.btn_remover = QPushButton("Remover selecionado")
        self.btn_remover.clicked.connect(self.remover_selecionado)
        self.btn_limpar = QPushButton("Limpar histórico")
        self.btn_limpar.clicked.connect(self.limpar_historico)

        self.label_historico = QLabel("Histórico de transcrições:")
        self.lista_historico = QListWidget()
        self.lista_historico.itemClicked.connect(self.abrir_do_historico)

        layout_principal = QHBoxLayout()
        layout_esquerda = QVBoxLayout()
        layout_direita = QVBoxLayout()

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.label_modelo)
        hlayout.addWidget(self.combo_modelos)
        hlayout.addWidget(self.label_idioma)
        hlayout.addWidget(self.combo_idioma)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_abrir)

        layout_esquerda.addLayout(hlayout)
        layout_esquerda.addWidget(self.btn_config)
        layout_esquerda.addWidget(self.label_status)
        layout_esquerda.addWidget(self.label_arquivo)
        layout_esquerda.addWidget(self.btn_transcrever)
        layout_esquerda.addWidget(self.progress)
        layout_esquerda.addWidget(self.drop_label)
        layout_esquerda.addWidget(self.drop_area)
        layout_esquerda.addWidget(self.texto_transcricao)

        layout_direita.addWidget(self.busca_historico)
        layout_direita.addWidget(self.label_historico)
        layout_direita.addWidget(self.lista_historico)
        layout_direita.addWidget(self.btn_remover)
        layout_direita.addWidget(self.btn_limpar)

        layout_principal.addLayout(layout_esquerda, 3)
        layout_principal.addLayout(layout_direita, 1)

        container = QWidget()
        container.setLayout(layout_principal)
        self.setCentralWidget(container)

        self.thread = None
        self._historico_cache = []

        self.carregar_historico()

    def carregar_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def salvar_config(self, novo_config):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(novo_config, f, indent=2, ensure_ascii=False)
        self.config = novo_config
        self.combo_modelos.setCurrentText(novo_config.get("modelo", "small"))
        idx_idioma = 0
        for i, (cod, nome) in enumerate(IDIOMAS):
            if cod == novo_config.get("idioma", "auto"):
                idx_idioma = i
                break
        self.combo_idioma.setCurrentIndex(idx_idioma)

    def abrir_configuracoes(self):
        dlg = ConfigDialog(self.config)
        if dlg.exec_():
            novo_config = dlg.get_config()
            self.salvar_config(novo_config)
            QMessageBox.information(self, "Configurações", "Salvo com sucesso!")

    def selecionar_arquivo(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Selecione um arquivo de áudio ou vídeo",
            "", "Áudio/Vídeo (*.mp3 *.mp4 *.wav *.m4a *.ogg *.flac)"
        )
        if fname:
            self.setar_arquivo(fname)

    def arquivo_arrastado(self, file_path):
        self.setar_arquivo(file_path)

    def setar_arquivo(self, caminho):
        self.caminho_arquivo = caminho
        self.label_arquivo.setText(f"Arquivo: {os.path.basename(caminho)}")

    def transcrever(self):
        if not self.caminho_arquivo:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo primeiro.")
            return

        modelo = self.combo_modelos.currentText()
        idioma = self.combo_idioma.currentData()
        self.texto_transcricao.setPlainText("Processando, aguarde...\n")
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.label_status.setText("Iniciando processamento...")
        QApplication.processEvents()

        self.thread = TranscricaoThread(self.caminho_arquivo, modelo, idioma)
        self.thread.progresso.connect(self.atualizar_progresso_detalhado)
        self.thread.resultado.connect(self.exibir_transcricao)
        self.thread.erro.connect(self.exibir_erro)
        self.thread.start()

    def atualizar_progresso_detalhado(self, valor, texto):
        self.progress.setValue(valor)
        self.label_status.setText(texto)

    def exibir_transcricao(self, texto):
        self.texto_transcricao.setPlainText(texto)
        self.progress.setValue(100)
        self.progress.setVisible(False)
        self.label_status.setText("Pronto!")
        self.adicionar_ao_historico()

    def exibir_erro(self, mensagem):
        self.texto_transcricao.setPlainText("Erro durante a transcrição:\n" + mensagem)
        self.progress.setVisible(False)
        self.label_status.setText("Erro!")

    def adicionar_ao_historico(self):
        base = os.path.splitext(os.path.basename(self.caminho_arquivo))[0]
        pasta = os.path.dirname(os.path.abspath(__file__))
        caminho_transcr = os.path.join(pasta, "Transcricoes", f"transcricao_{base}.txt")
        idioma_cod = self.combo_idioma.currentData()
        idioma_nome = self.combo_idioma.currentText()
        data = {
            "arquivo": caminho_transcr,
            "nome": f"transcricao_{base}.txt",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "idioma": idioma_cod
        }
        historico = []
        if os.path.exists(HISTORICO_PATH):
            try:
                with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
                    historico = json.load(f)
            except Exception:
                historico = []
        historico = [h for h in historico if h["arquivo"] != data["arquivo"]]
        historico.insert(0, data)
        max_itens = self.config.get("max_historico", 20)
        historico = historico[:max_itens]
        with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
            json.dump(historico, f, indent=2, ensure_ascii=False)
        self.carregar_historico()

    def carregar_historico(self):
        if os.path.exists(HISTORICO_PATH):
            try:
                with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
                    historico = json.load(f)
                self._historico_cache = historico
            except Exception:
                self._historico_cache = []
        else:
            self._historico_cache = []
        self.filtrar_historico(self.busca_historico.text())

    def filtrar_historico(self, texto):
        texto = texto.strip().lower()
        self.lista_historico.clear()
        for h in getattr(self, '_historico_cache', []):
            nome = h['nome'].lower()
            data_str = h['data'].lower()
            idioma_str = h.get('idioma', 'auto')
            idioma_nome = next((n for c, n in IDIOMAS if c == idioma_str), idioma_str)
            if texto in nome or texto in data_str or texto in idioma_nome.lower():
                display = f"{h['nome']}  ({h['data']}, {idioma_nome})"
                self.lista_historico.addItem(display)

    def abrir_do_historico(self, item):
        idx = self.lista_historico.currentRow()
        filtrados = []
        texto = self.busca_historico.text().strip().lower()
        for h in getattr(self, '_historico_cache', []):
            nome = h['nome'].lower()
            data_str = h['data'].lower()
            idioma_str = h.get('idioma', 'auto')
            idioma_nome = next((n for c, n in IDIOMAS if c == idioma_str), idioma_str)
            if texto in nome or texto in data_str or texto in idioma_nome.lower():
                filtrados.append(h)
        if idx >= len(filtrados):
            return
        caminho = filtrados[idx]["arquivo"]
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read()
            self.texto_transcricao.setPlainText(conteudo)
        else:
            QMessageBox.warning(self, "Aviso", "Arquivo de transcrição não encontrado!")

    def remover_selecionado(self):
        idx = self.lista_historico.currentRow()
        texto = self.busca_historico.text().strip().lower()
        filtrados = []
        for h in getattr(self, '_historico_cache', []):
            nome = h['nome'].lower()
            data_str = h['data'].lower()
            idioma_str = h.get('idioma', 'auto')
            idioma_nome = next((n for c, n in IDIOMAS if c == idioma_str), idioma_str)
            if texto in nome or texto in data_str or texto in idioma_nome.lower():
                filtrados.append(h)
        if idx < 0 or idx >= len(filtrados):
            return
        to_remove = filtrados[idx]
        self._historico_cache = [h for h in self._historico_cache if h != to_remove]
        with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
            json.dump(self._historico_cache, f, indent=2, ensure_ascii=False)
        self.carregar_historico()

    def limpar_historico(self):
        resp = QMessageBox.question(self, "Limpar histórico", "Tem certeza que deseja apagar todo o histórico?")
        if resp == QMessageBox.Yes:
            self._historico_cache = []
            if os.path.exists(HISTORICO_PATH):
                os.remove(HISTORICO_PATH)
            self.carregar_historico()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranscricaoApp()
    window.show()
    sys.exit(app.exec_())