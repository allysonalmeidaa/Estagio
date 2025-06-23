import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
# Importe corretamente seu script onde está a função processar_video
from Processamento_video import processar_video  # Altere para o nome do seu arquivo de conversão

class ConversaoTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Campo para URL ou caminho do arquivo
        self.label_origem = QLabel("URL do vídeo ou caminho do arquivo local:")
        self.input_origem = QLineEdit()
        self.btn_arquivo = QPushButton("Selecionar arquivo")
        self.btn_arquivo.clicked.connect(self.selecionar_arquivo)

        origem_layout = QHBoxLayout()
        origem_layout.addWidget(self.input_origem)
        origem_layout.addWidget(self.btn_arquivo)

        layout.addWidget(self.label_origem)
        layout.addLayout(origem_layout)

        # Checkboxes para formatos
        self.check_telefonia = QCheckBox("Padrão Telefonia (WAV 8kHz)")
        self.check_hq = QCheckBox("Alta Qualidade (FLAC 96kHz)")
        self.check_podcast = QCheckBox("Podcast (M4A)")
        self.check_stream = QCheckBox("Streaming (OGG)")
        self.check_radio = QCheckBox("Rádio FM (WAV)")
        self.check_whatsapp = QCheckBox("WhatsApp (OGG/OPUS)")

        layout.addWidget(QLabel("Formatos de saída desejados:"))
        layout.addWidget(self.check_telefonia)
        layout.addWidget(self.check_hq)
        layout.addWidget(self.check_podcast)
        layout.addWidget(self.check_stream)
        layout.addWidget(self.check_radio)
        layout.addWidget(self.check_whatsapp)

        # Botão processar
        self.btn_processar = QPushButton("Processar")
        self.btn_processar.clicked.connect(self.processar)
        layout.addWidget(self.btn_processar)

        # Área de resultado
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.setLayout(layout)

    def selecionar_arquivo(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Selecione um arquivo de vídeo ou áudio",
            "", "Vídeo/Áudio (*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        if fname:
            self.input_origem.setText(fname)

    def processar(self):
        origem = self.input_origem.text().strip()
        if not origem:
            QMessageBox.warning(self, "Aviso", "Informe uma URL ou selecione um arquivo.")
            return
        formatos = []
        if self.check_telefonia.isChecked(): formatos.append('1')
        if self.check_hq.isChecked(): formatos.append('2')
        if self.check_podcast.isChecked(): formatos.append('3')
        if self.check_stream.isChecked(): formatos.append('4')
        if self.check_radio.isChecked(): formatos.append('5')
        if self.check_whatsapp.isChecked(): formatos.append('6')
        if not formatos:
            QMessageBox.warning(self, "Aviso", "Selecione ao menos um formato de saída!")
            return
        saida_dir = os.path.join(os.path.dirname(__file__), "saida_audio")
        os.makedirs(saida_dir, exist_ok=True)

        self.result_area.setPlainText("Processando...\n")
        try:
            caminho_video, arquivos_gerados = processar_video(origem, saida_dir, formatos)
            if arquivos_gerados:
                msg = "Arquivos gerados com sucesso:\n\n"
                for f in arquivos_gerados:
                    msg += f"{os.path.basename(f)}\n"
                self.result_area.setPlainText(msg)
            else:
                self.result_area.setPlainText("Nenhum arquivo foi gerado.")
        except Exception as e:
            self.result_area.setPlainText(f"Erro durante o processamento:\n{str(e)}")