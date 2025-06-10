import os
import whisper
from pyannote.audio import Pipeline
from datetime import timedelta
import ffmpeg
from dotenv import load_dotenv

def format_timestamp(seconds):
    return str(timedelta(seconds=float(seconds))).split('.')[0]

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

def transcrever_com_diarizacao(caminho_arquivo, modelo_escolhido, idioma=None, progresso_callback=None):
    """
    Adiciona parâmetro idioma (código do idioma ou None para detecção automática).
    """
    load_dotenv()
    PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
    PASTA_TRANSCRICOES = os.path.join(PASTA_SCRIPT, "Transcricoes")
    if not os.path.exists(PASTA_TRANSCRICOES):
        os.makedirs(PASTA_TRANSCRICOES)
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
    if not HUGGINGFACE_TOKEN:
        raise ValueError("Configure a variável HUGGINGFACE_TOKEN no seu arquivo .env")

    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    caminho_audio_temp = None

    if progresso_callback:
        progresso_callback(5, "Extraindo arquivo")

    ext = os.path.splitext(caminho_arquivo)[1].lower()
    if ext not in ['.wav', '.flac']:
        caminho_audio_temp = os.path.join(PASTA_SCRIPT, f"temp_{nome_base}.wav")
        try:
            stream = ffmpeg.input(caminho_arquivo)
            stream = ffmpeg.output(stream, caminho_audio_temp, acodec='pcm_s16le', ac=1, ar='16k')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            caminho_arquivo_para_diarizacao = caminho_audio_temp
        except ffmpeg.Error as e:
            raise RuntimeError("Erro ao extrair áudio com FFmpeg: " + e.stderr.decode())
    else:
        caminho_arquivo_para_diarizacao = caminho_arquivo

    if progresso_callback:
        progresso_callback(20, "Diarizando falantes")
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=HUGGINGFACE_TOKEN
        )
        diarization = pipeline(caminho_arquivo_para_diarizacao)
        if progresso_callback:
            progresso_callback(40, "Diarização concluída")

        if progresso_callback:
            progresso_callback(50, "Transcrevendo com Whisper")
        modelo = whisper.load_model(modelo_escolhido)
        # Chama o Whisper com o idioma apropriado
        kwargs = {}
        if idioma and idioma != "auto":
            kwargs["language"] = idioma
        resultado = modelo.transcribe(caminho_arquivo_para_diarizacao, **kwargs)
        if progresso_callback:
            progresso_callback(80, "Transcrição concluída")

        if progresso_callback:
            progresso_callback(85, "Combinando falantes e transcrição")
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
        segments = remove_repeticoes(segments)

        if progresso_callback:
            progresso_callback(90, "Salvando transcrição")
        caminho_transcr = os.path.join(PASTA_TRANSCRICOES, f"transcricao_{nome_base}.txt")
        with open(caminho_transcr, "w", encoding="utf-8") as f:
            if not segments or len(segments) == 0:
                mensagem = "AVISO: Nenhum segmento de fala foi detectado ou todos os segmentos foram filtrados.\n"
                f.write(mensagem)
            else:
                for segment in segments:
                    f.write(f"[{format_timestamp(segment['start'])} -> {format_timestamp(segment['end'])}] {segment['speaker']}: {segment['text']}\n\n")

        # Só traduz se idioma for diferente de inglês
        if idioma != "en":
            if progresso_callback:
                progresso_callback(92, "Traduzindo para o inglês")
            resultado_traduzido = modelo.transcribe(caminho_arquivo_para_diarizacao, task="translate", **kwargs)
            if progresso_callback:
                progresso_callback(95, "Salvando tradução em inglês")
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

        if progresso_callback:
            progresso_callback(100, "Processo concluído!")

        if not segments or len(segments) == 0:
            return "Nenhum segmento de fala foi detectado ou todos os segmentos foram filtrados."
        else:
            texto_interface = ""
            for segment in segments:
                texto_interface += f"[{format_timestamp(segment['start'])} -> {format_timestamp(segment['end'])}] {segment['speaker']}: {segment['text']}\n\n"
            return texto_interface

    finally:
        if caminho_audio_temp and os.path.exists(caminho_audio_temp):
            try:
                os.remove(caminho_audio_temp)
            except Exception:
                pass