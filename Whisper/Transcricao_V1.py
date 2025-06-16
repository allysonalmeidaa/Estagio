import whisper
import os
import torch
from pyannote.audio import Pipeline
from datetime import timedelta
import ffmpeg
from dotenv import load_dotenv  # NOVO!

# Carregar variáveis de ambiente do .env
load_dotenv()

# Caminho das pastas
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_AUDIOS = os.path.join(PASTA_SCRIPT, "audios")
PASTA_TRANSCRICOES = os.path.join(PASTA_SCRIPT, "Transcricoes")

# Criar pasta de transcrições se não existir
if not os.path.exists(PASTA_TRANSCRICOES):
    os.makedirs(PASTA_TRANSCRICOES)

# Token do Hugging Face via variável de ambiente
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
if not HUGGINGFACE_TOKEN:
    raise ValueError("Por favor, configure a variável de ambiente HUGGINGFACE_TOKEN no seu arquivo .env")

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

modelos_disponiveis = ["tiny", "base", "small", "medium", "large"]

print("Modelos disponíveis:")
for i, modelo in enumerate(modelos_disponiveis, 1):
    print(f"{i}. {modelo}")

while True:
    modelo_escolhido = input("Digite o nome do modelo que deseja usar (tiny, base, small, medium, large): ").strip().lower()
    if modelo_escolhido in modelos_disponiveis:
        break
    else:
        print("Modelo inválido. Por favor, escolha entre: tiny, base, small, medium, large.")

extensoes_validas = (".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac")
arquivos_disponiveis = [arq for arq in os.listdir(PASTA_AUDIOS) if arq.lower().endswith(extensoes_validas)]

if not arquivos_disponiveis:
    print("Nenhum arquivo de áudio ou vídeo suportado encontrado na pasta 'audios'.")
    exit()

print("\nArquivos de áudio/vídeo disponíveis:")
for i, arquivo in enumerate(arquivos_disponiveis, 1):
    print(f"{i}. {arquivo}")

while True:
    arquivo_escolhido = input("Digite o nome do arquivo que deseja transcrever (exatamente como aparece acima): ").strip()
    if arquivo_escolhido in arquivos_disponiveis:
        break
    else:
        print("Arquivo inválido. Por favor, escolha um dos arquivos listados acima.")

nome_base = os.path.splitext(arquivo_escolhido)[0]
caminho_arquivo = os.path.join(PASTA_AUDIOS, arquivo_escolhido)

if arquivo_escolhido.lower().endswith(('.mp4', '.avi', '.mkv')):
    print("\nExtraindo áudio do arquivo de vídeo...")
    caminho_audio_temp = os.path.join(PASTA_SCRIPT, f"temp_{nome_base}.wav")
    try:
        stream = ffmpeg.input(caminho_arquivo)
        stream = ffmpeg.output(stream, caminho_audio_temp, acodec='pcm_s16le', ac=1, ar='16k')
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        print("Áudio extraído com sucesso!")
        caminho_arquivo_para_diarizacao = caminho_audio_temp
    except ffmpeg.Error as e:
        print("Erro ao extrair áudio:", e.stderr.decode())
        exit(1)
else:
    caminho_arquivo_para_diarizacao = caminho_arquivo

try:
    print("\nInicializando pipeline de diarização...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=HUGGINGFACE_TOKEN
    )

    print("Realizando diarização do áudio...")
    diarization = pipeline(caminho_arquivo_para_diarizacao)

    print("\nCarregando modelo Whisper...")
    modelo = whisper.load_model(modelo_escolhido)

    print("Realizando transcrição...")
    resultado = modelo.transcribe(caminho_arquivo)

    print("\nCombinando resultados da diarização com a transcrição...")
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

    print("Salvando transcrição com identificação de falantes...")
    caminho_transcr = os.path.join(PASTA_TRANSCRICOES, f"transcricao_{nome_base}.txt")
    with open(caminho_transcr, "w", encoding="utf-8") as f:
        if not segments or len(segments) == 0:
            mensagem = "AVISO: Nenhum segmento de fala foi detectado ou todos os segmentos foram filtrados.\n"
            f.write(mensagem)
            print(mensagem)
        else:
            for segment in segments:
                f.write(f"[{format_timestamp(segment['start'])} -> {format_timestamp(segment['end'])}] {segment['speaker']}: {segment['text']}\n\n")

    print(f"\nTranscrição com identificação de falantes salva como 'transcricao_{nome_base}.txt'")

    print("\nRealizando tradução para inglês...")
    resultado_traduzido = modelo.transcribe(caminho_arquivo, task="translate")

    caminho_trad = os.path.join(PASTA_TRANSCRICOES, f"transcricao_{nome_base}_ingles.txt")
    with open(caminho_trad, "w", encoding="utf-8") as f:
        if not segments or len(segments) == 0:
            mensagem = "WARNING: No speech segments were detected or all segments were filtered.\n"
            f.write(mensagem)
            print(mensagem)
        else:
            for segment in segments:
                translated_text = ""
                for trans_segment in resultado_traduzido["segments"]:
                    if (trans_segment["start"] <= segment["end"] and 
                        trans_segment["end"] >= segment["start"]):
                        translated_text += " " + trans_segment["text"]
                if translated_text.strip():
                    f.write(f"[{format_timestamp(segment['start'])} -> {format_timestamp(segment['end'])}] {segment['speaker']}: {translated_text.strip()}\n\n")

    print(f"Transcrição em inglês com identificação de falantes salva como 'transcricao_{nome_base}_ingles.txt'")

except Exception as e:
    print(f"\nErro durante o processamento: {str(e)}")
    raise

finally:
    if 'caminho_audio_temp' in locals():
        try:
            os.remove(caminho_audio_temp)
            print("\nArquivo de áudio temporário removido.")
        except:
            print("\nNão foi possível remover o arquivo de áudio temporário.")