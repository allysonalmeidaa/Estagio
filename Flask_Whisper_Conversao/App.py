import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from Transcricao import transcrever_com_diarizacao
from Conversao import converter_audio, baixar_youtube

# NOVO: Importa Google Translate para tradução automática
try:
    from googletrans import Translator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

UPLOAD_FOLDER = "Uploads"
TRANSCRICOES_FOLDER = "Transcricoes"
CONVERSOES_FOLDER = "Conversoes"
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'wav', 'm4a', 'ogg', 'flac', 'webm', 'mkv'}

IDIOMAS = [
    ("auto", "Detectar automático"),
    ("pt", "Português"),
    ("en", "Inglês"),
    ("es", "Espanhol"),
    ("fr", "Francês"),
    ("de", "Alemão"),
]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRICOES_FOLDER, exist_ok=True)
os.makedirs(CONVERSOES_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/transcricao', methods=['GET', 'POST'])
def transcricao():
    transcricao = None
    filename = None
    filename_en = None
    error = None
    modelo = request.form.get("modelo", "small")
    idioma = request.form.get("idioma", "auto")
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename_local = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_local)
            file.save(filepath)
            try:
                texto = transcrever_com_diarizacao(filepath, modelo, idioma)
                nome_saida = f"transcricao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                saida_path = os.path.join(TRANSCRICOES_FOLDER, nome_saida)
                with open(saida_path, "w", encoding="utf-8") as f:
                    f.write(texto)
                transcricao = texto
                filename = nome_saida
                # Busca ou gera versão traduzida para inglês
                nome_saida_en = nome_saida.replace('.txt', '_ingles.txt')
                saida_path_en = os.path.join(TRANSCRICOES_FOLDER, nome_saida_en)
                if not os.path.exists(saida_path_en):
                    # Traduz automaticamente se possível
                    if HAS_TRANSLATOR:
                        translator = Translator()
                        try:
                            traduzido = translator.translate(texto, src='pt', dest='en').text
                            with open(saida_path_en, "w", encoding="utf-8") as f:
                                f.write(traduzido)
                        except Exception as e:
                            print(f"Erro ao traduzir para inglês: {e}")
                    # Se não tem tradutor, não gera arquivo
                if os.path.exists(saida_path_en):
                    filename_en = nome_saida_en
            except Exception as e:
                error = f"Erro na transcrição: {e}"
        else:
            error = "Arquivo inválido ou não suportado."
    return render_template(
        "transcricao.html",
        idiomas=IDIOMAS,
        transcricao=transcricao,
        filename=filename,
        filename_en=filename_en,
        error=error,
        modelo=modelo,
        idioma=idioma
    )

@app.route('/conversao', methods=['GET', 'POST'])
def conversao():
    resultado_conversao = None
    video_original = None
    audio_extraido = None
    error = None
    if request.method == 'POST':
        file = request.files.get('file')
        youtube_link = request.form.get('youtube_link')
        formato_saida = request.form.get('formato_saida', 'mp3').lower()
        filename = None
        filepath = None
        # Se tiver YouTube, baixa primeiro
        if youtube_link and youtube_link.strip():
            try:
                filename, filepath = baixar_youtube(youtube_link, UPLOAD_FOLDER)
                video_original = filename
            except Exception as e:
                error = f"Erro ao baixar do YouTube: {e}"
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            video_original = filename
        else:
            error = "Arquivo inválido, não suportado ou link do YouTube ausente."
        # Se OK, faz conversão e extração
        if filepath and os.path.exists(filepath):
            try:
                # Extração de áudio
                nome_audio = f"audio_extraido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                path_audio = os.path.join(CONVERSOES_FOLDER, nome_audio)
                converter_audio(filepath, path_audio, 'mp3')
                audio_extraido = nome_audio
                # Conversão para formato escolhido
                nome_saida = f"convertido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{formato_saida}"
                saida_path = os.path.join(CONVERSOES_FOLDER, nome_saida)
                converter_audio(filepath, saida_path, formato_saida)
                resultado_conversao = nome_saida
            except Exception as e:
                error = f"Erro ao converter: {e}"
    return render_template("conversao.html", resultado_conversao=resultado_conversao, video_original=video_original, audio_extraido=audio_extraido, error=error)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(TRANSCRICOES_FOLDER, filename, as_attachment=True)

@app.route('/baixar_conversao/<filename>')
def baixar_conversao(filename):
    return send_from_directory(CONVERSOES_FOLDER, filename, as_attachment=True)

@app.route('/sobre')
def sobre():
    return render_template("sobre.html")

if __name__ == '__main__':
    app.run(debug=True)