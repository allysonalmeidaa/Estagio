# Importação de módulos do sistema e PyQt5 para criar a interface gráfica
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QFileDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QComboBox, QMessageBox, QProgressBar
)
from PyQt5.QtCore import QThread, pyqtSignal
from transcricao_core import transcrever_com_diarizacao # Função de transcrição (núcleo)

# Thread para rodar a transcrição em background, sem travar a interface
class TranscricaoThread(QThread):
    progresso = pyqtSignal(int)         # Sinal: atualiza barra de progresso
    resultado = pyqtSignal(str)         # Sinal: resultado final da transcrição
    erro = pyqtSignal(str)              # Sinal: erro durante transcrição

    def __init__(self, caminho, modelo):
        super().__init__()
        self.caminho = caminho          # Caminho do arquivo a ser transcrito
        self.modelo = modelo            # Modelo Whisper escolhido

    def run(self):
        try:
            # Sinaliza início do processamento (exemplo fixo, pode ser detalhado)
            self.progresso.emit(10)
            # Chama função que processa a transcrição e diarização
            texto = transcrever_com_diarizacao(self.caminho, self.modelo)
            # Sinaliza fim do processamento
            self.progresso.emit(100)
            # Envia resultado para interface
            self.resultado.emit(texto)
        except Exception as e:
            # Caso dê erro, envia mensagem de erro para interface
            self.erro.emit(str(e))

# Janela principal da aplicação
class TranscricaoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcrição com Whisper (Qt)")
        self.setGeometry(200, 200, 800, 600)     # Tamanho inicial da janela

        self.caminho_arquivo = ""                # Nome do arquivo escolhido
        self.label_arquivo = QLabel("Arquivo: nenhum selecionado")
        self.btn_abrir = QPushButton("Selecionar arquivo")
        self.btn_abrir.clicked.connect(self.selecionar_arquivo) # Ação ao clicar no botão

        self.label_modelo = QLabel("Modelo Whisper:")
        self.combo_modelos = QComboBox()
        self.combo_modelos.addItems(["tiny", "base", "small", "medium", "large"])
        self.combo_modelos.setCurrentText("small") # Modelo padrão selecionado

        self.btn_transcrever = QPushButton("Transcrever")
        self.btn_transcrever.clicked.connect(self.transcrever)   # Ação ao clicar

        self.texto_transcricao = QTextEdit()      # Área onde aparece a transcrição
        self.texto_transcricao.setReadOnly(True)

        self.progress = QProgressBar()            # Barra de progresso
        self.progress.setValue(0)
        self.progress.setVisible(False)           # Só aparece durante processamento

        # Layouts para organizar os elementos na tela
        layout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.label_modelo)
        hlayout.addWidget(self.combo_modelos)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_abrir)

        layout.addLayout(hlayout)
        layout.addWidget(self.label_arquivo)
        layout.addWidget(self.btn_transcrever)
        layout.addWidget(self.progress)
        layout.addWidget(self.texto_transcricao)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)          # Define o layout central da janela

        self.thread = None                        # Thread de transcrição (será criada no botão)

    # Abre janela para selecionar arquivo de áudio/vídeo
    def selecionar_arquivo(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Selecione um arquivo de áudio ou vídeo",
            "", "Áudio/Vídeo (*.mp3 *.mp4 *.wav *.m4a *.ogg *.flac)"
        )
        if fname:
            self.caminho_arquivo = fname
            self.label_arquivo.setText(f"Arquivo: {os.path.basename(fname)}")

    # Inicia o processo de transcrição ao clicar no botão
    def transcrever(self):
        if not self.caminho_arquivo:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo primeiro.")
            return

        modelo = self.combo_modelos.currentText()
        self.texto_transcricao.setPlainText("Processando, aguarde...\n")
        self.progress.setVisible(True)
        self.progress.setValue(0)
        QApplication.processEvents() # Atualiza interface imediatamente

        # Cria thread para rodar a transcrição em background
        self.thread = TranscricaoThread(self.caminho_arquivo, modelo)
        self.thread.progresso.connect(self.progress.setValue)      # Conecta progresso à barra
        self.thread.resultado.connect(self.exibir_transcricao)     # Conecta saída de texto
        self.thread.erro.connect(self.exibir_erro)                 # Conecta erro
        self.thread.start()

    # Exibe resultado da transcrição no campo de texto
    def exibir_transcricao(self, texto):
        self.texto_transcricao.setPlainText(texto)
        self.progress.setValue(100)
        self.progress.setVisible(False)

    # Exibe mensagem de erro, caso ocorra
    def exibir_erro(self, mensagem):
        self.texto_transcricao.setPlainText("Erro durante a transcrição:\n" + mensagem)
        self.progress.setVisible(False)

# Executa o aplicativo
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranscricaoApp()
    window.show()
    sys.exit(app.exec_())