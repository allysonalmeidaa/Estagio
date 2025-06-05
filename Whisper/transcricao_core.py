# Importações necessárias: manipulação de arquivos, modelos de transcrição e diarização, utilitários
import os
import whisper
from pyannote.audio import Pipeline
from datetime import timedelta
import ffmpeg
from dotenv import load_dotenv

# Formata segundos em "HH:MM:SS"
def format_timestamp(seconds):
    from datetime import timedelta
    return str(timedelta(seconds=float(seconds))).split('.')[0]

# Remove repetições de segmentos de texto muito parecidos
def remove_repeticoes(segments):
    if not segments:
        return segments

    cleaned_segments = []
    previous_segment = None
    
    for segment in segments:
        if previous_segment is None:
            cleaned_segments.append(segment)
            previous_segment = segment
            continue
            
        current_text = segment["text"].strip().lower()
        previous_text = previous_segment["text"].strip().lower()
        cleaned_current = ''.join(c for c in current_text if c.isalnum() or c.isspace())
        cleaned_prev = ''.join(c for c in previous_text if c.isalnum() or c.isspace())
        if (abs(len(cleaned_current) - len(cleaned_prev)) > 10 or  
            (cleaned_current not in cleaned_prev and cleaned_prev not in cleaned_current)):
            cleaned_segments.append(segment)
            previous_segment = segment
    return cleaned_segments

# Função principal: transcreve e faz diarização do arquivo, salva txt e retorna resumo para interface
def transcrever_com_diarizacao(caminho_arquivo, modelo_escolhido):
    load_dotenv()  # Carrega variáveis do .env (token HuggingFace)
    PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
    PASTA_TRANSCRICOES = os.path.join(PASTA_SCRIPT, "Transcricoes")

    # Cria pasta de transcrições, se não existir
    if not os.path.exists(PASTA_TRANSCRICOES):
        os.makedirs(PASTA_TRANSCRICOES)

    # Token necessário para pipeline de diarização
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
    if not HUGGINGFACE_TOKEN:
        raise ValueError("Configure a variável HUGGINGFACE_TOKEN no seu arquivo .env")

    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    caminho_audio_temp = None

    # Se o arquivo for vídeo, extrai o áudio para processamento
    if caminho_arquivo.lower().endswith(('.mp4', '.avi', '.mkv')):
        caminho_audio_temp = os.path.join(PASTA_SCRIPT, f"temp_{nome_base}.wav")
        try:
            stream = ffmpeg.input(caminho_arquivo)
            stream = ffmpeg.output(stream, caminho_audio_temp, acodec='pcm_s16le', ac=1, ar='16k')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            caminho_arquivo_para_diarizacao = caminho_audio_temp
        except ffmpeg.Error as e:
            raise RuntimeError("Erro ao extrair áudio: " + e.stderr.decode())
    else:
        caminho_arquivo_para_diarizacao = caminho_arquivo

    try:
        # Inicializa pipeline de diarização (identificação de falantes)
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=HUGGINGFACE_TOKEN
        )
        diarization = pipeline(caminho_arquivo_para_diarizacao)

        # Carrega modelo Whisper e faz transcrição do arquivo
        modelo = whisper.load_model(modelo_escolhido)
        resultado = modelo.transcribe(caminho_arquivo)

        # Combina intervalos/falantes da diarização com textos da transcrição
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start_time = turn.start
            end_time = turn.end
            segment_text = ""
            for segment in resultado["segments"]:
                seg_start = segment["start"]
                seg_end = segment["end"]
                if (seg_start <= end_time and seg_end >= start_time):
                    segment_text += " " + segment["text"]
            if segment_text.strip():
                segments.append({
                    "speaker": speaker,
                    "start": start_time,
                    "end": end_time,
                    "text": segment_text.strip()
                })

        segments = remove_repeticoes(segments)  # Limpa repetições de texto

        # Salva transcrição em português com falantes
        caminho_transcr = os.path.join(PASTA_TRANSCRICOES, f"transcricao_{nome_base}.txt")
        with open(caminho_transcr, "w", encoding="utf-8") as f:
            if not segments or len(segments) == 0:
                mensagem = "AVISO: Nenhum segmento de fala foi detectado ou todos os segmentos foram filtrados.\n"
                f.write(mensagem)
            else:
                for segment in segments:
                    f.write(f"[{format_timestamp(segment['start'])} -> {format_timestamp(segment['end'])}] {segment['speaker']}: {segment['text']}\n\n")

        # Tradução automática para inglês, salva em outro arquivo
        resultado_traduzido = modelo.transcribe(caminho_arquivo, task="translate")
        caminho_trad = os.path.join(PASTA_TRANSCRICOES, f"transcricao_{nome_base}_ingles.txt")
        with open(caminho_trad, "w", encoding="utf-8") as f:
            if not segments or len(segments) == 0:
                mensagem = "WARNING: No speech segments were detected or all segments were filtered.\n"
                f.write(mensagem)
            else:
                for segment in segments:
                    translated_text = ""
                    for trans_segment in resultado_traduzido["segments"]:
                        if (trans_segment["start"] <= segment["end"] and 
                            trans_segment["end"] >= segment["start"]):
                            translated_text += " " + trans_segment["text"]
                    if translated_text.strip():
                        f.write(f"[{format_timestamp(segment['start'])} -> {format_timestamp(segment['end'])}] {segment['speaker']}: {translated_text.strip()}\n\n")

        # Retorna resumo da transcrição para exibir na interface
        if not segments or len(segments) == 0:
            return "Nenhum segmento de fala foi detectado ou todos os segmentos foram filtrados."
        else:
            texto_interface = ""
            for segment in segments:
                texto_interface += f"[{format_timestamp(segment['start'])} -> {format_timestamp(segment['end'])}] {segment['speaker']}: {segment['text']}\n\n"
            return texto_interface

    finally:
        # Remove áudio temporário se foi criado (em caso de vídeo)
        if caminho_audio_temp and os.path.exists(caminho_audio_temp):
            try:
                os.remove(caminho_audio_temp)
            except Exception:
                pass  # Se não conseguir remover, apenas ignora (não trava o app)