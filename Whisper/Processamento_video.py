import os
import subprocess
import yt_dlp
from datetime import datetime

def obter_timestamp_formatado():
    """Retorna um timestamp formatado para usar no nome dos arquivos."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def criar_diretorio_saida():
    """Cria um diretório para armazenar os arquivos processados dentro da pasta whisper."""
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    diretorio_saida = os.path.join(diretorio_script, "saida_audio")
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)
    return diretorio_saida

def verifica_arquivo_local(caminho):
    """Verifica se o caminho fornecido é um arquivo local."""
    caminho = caminho.strip('"\'')
    return os.path.isfile(caminho)

def verifica_url(texto):
    """Verifica se o texto é uma URL."""
    return texto.strip('"\'').startswith(('http://', 'https://', 'www.'))

def processar_video_local(caminho_origem, caminho_saida):
    """Processa um arquivo de vídeo local mantendo o áudio."""
    try:
        caminho_origem = caminho_origem.strip('"\'')
        if not os.path.exists(caminho_origem):
            print(f"Erro: Arquivo não encontrado: {caminho_origem}")
            return None

        timestamp = obter_timestamp_formatado()
        nome_arquivo = os.path.basename(caminho_origem)
        nome_base = os.path.splitext(nome_arquivo)[0]
        destino = os.path.join(caminho_saida, f"video_{timestamp}_{nome_base}.mp4")

        print(f"\nProcessando arquivo local: {caminho_origem}")
        print(f"Para: {destino}")

        comando = [
            'ffmpeg',
            '-i', caminho_origem,
            '-c:v', 'copy',     # Copia o stream de vídeo sem recodificar
            '-c:a', 'aac',      # Converte áudio para AAC
            '-b:a', '192k',     # Bitrate do áudio
            '-y',               # Sobrescreve se existir
            destino
        ]

        processo = subprocess.run(comando, capture_output=True, text=True)
        
        if processo.returncode == 0 and os.path.exists(destino):
            print("Vídeo processado com sucesso!")
            return destino
        else:
            print(f"Erro ao processar vídeo: {processo.stderr}")
            return None

    except Exception as e:
        print(f"Erro ao processar arquivo local: {str(e)}")
        return None

def baixar_do_youtube(url, caminho_saida):
    """Baixa vídeo do YouTube com áudio."""
    try:
        timestamp = obter_timestamp_formatado()
        opcoes_ydl = {
            'format': 'best',  # Baixa a melhor qualidade que já inclui áudio e vídeo
            'outtmpl': os.path.join(caminho_saida, f"video_{timestamp}_%(title)s.%(ext)s"),
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'prefer_ffmpeg': True,
        }
        
        with yt_dlp.YoutubeDL(opcoes_ydl) as ydl:
            print("\nBaixando vídeo do YouTube...")
            info = ydl.extract_info(url, download=True)
            caminho_video = ydl.prepare_filename(info)
            
            # Limpa arquivos temporários .m4a
            diretorio_base = os.path.dirname(caminho_video)
            nome_base = os.path.splitext(os.path.basename(caminho_video))[0]
            for arquivo in os.listdir(diretorio_base):
                if arquivo.endswith('.m4a') and nome_base in arquivo:
                    os.remove(os.path.join(diretorio_base, arquivo))
            
            return caminho_video
    except Exception as e:
        print(f"Erro ao baixar do YouTube: {str(e)}")
        return None

def extrair_audio(caminho_video, caminho_saida):
    """Extrai o áudio do vídeo com configurações otimizadas."""
    try:
        timestamp = obter_timestamp_formatado()
        nome_base = os.path.splitext(os.path.basename(caminho_video))[0]
        caminho_audio = os.path.join(caminho_saida, f"audio_{timestamp}_{nome_base}.mp3")
        
        comando = [
            'ffmpeg',
            '-i', caminho_video,
            '-vn',                # Remove vídeo
            '-acodec', 'libmp3lame',  # Codec MP3
            '-ab', '192k',        # Bitrate
            '-ar', '44100',       # Sample rate
            '-af', 'volume=2.0',  # Aumenta volume
            '-y',                 # Sobrescreve se existir
            caminho_audio
        ]
        
        print("\nExtraindo áudio...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        
        if processo.returncode == 0 and os.path.exists(caminho_audio):
            if os.path.getsize(caminho_audio) > 0:
                print(f"Áudio extraído com sucesso: {caminho_audio}")
                return caminho_audio
            else:
                print("Erro: Arquivo de áudio gerado está vazio")
                return None
        else:
            print(f"Erro ao extrair áudio: {processo.stderr}")
            return None
            
    except Exception as e:
        print(f"Erro ao extrair áudio: {str(e)}")
        return None

def converter_para_telefonia(caminho_audio, caminho_saida):
    """Converte o áudio para o padrão de telefonia."""
    try:
        timestamp = obter_timestamp_formatado()
        nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
        caminho_telefonia = os.path.join(caminho_saida, f"telefonia_{timestamp}_{nome_base}.wav")
        
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-ar', '8000',        # Sample rate para telefonia
            '-ac', '1',           # Mono
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-af', 'volume=3.0,highpass=f=300,lowpass=f=3400',  # Filtros de áudio
            '-y',                 # Sobrescreve se existir
            caminho_telefonia
        ]
        
        print("\nConvertendo para formato telefônico...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        
        if processo.returncode == 0 and os.path.exists(caminho_telefonia):
            if os.path.getsize(caminho_telefonia) > 0:
                print(f"Conversão concluída: {caminho_telefonia}")
                return caminho_telefonia
            else:
                print("Erro: Arquivo de áudio telefônico gerado está vazio")
                return None
        else:
            print(f"Erro na conversão: {processo.stderr}")
            return None
            
    except Exception as e:
        print(f"Erro na conversão telefônica: {str(e)}")
        return None

def converter_para_alta_qualidade(caminho_audio, caminho_saida):
    """Converte para áudio de alta qualidade (FLAC)."""
    try:
        timestamp = obter_timestamp_formatado()
        nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
        caminho_hq = os.path.join(caminho_saida, f"hq_{timestamp}_{nome_base}.flac")
        
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-c:a', 'flac',        # Codec FLAC (sem perdas)
            '-ar', '96000',        # Sample rate alto
            '-bits_per_raw_sample', '24',  # Profundidade de bits
            '-y',                  # Sobrescreve se existir
            caminho_hq
        ]
        
        print("\nConvertendo para formato de alta qualidade (FLAC)...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_hq if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão HQ: {str(e)}")
        return None

def converter_para_podcast(caminho_audio, caminho_saida):
    """Converte para formato ideal para podcasts."""
    try:
        timestamp = obter_timestamp_formatado()
        nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
        caminho_podcast = os.path.join(caminho_saida, f"podcast_{timestamp}_{nome_base}.m4a")
        
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-c:a', 'aac',         # Codec AAC
            '-b:a', '192k',        # Bitrate bom para voz
            '-ar', '44100',        # Sample rate padrão
            '-af', 'loudnorm',     # Normalização de volume
            '-y',                  # Sobrescreve se existir
            caminho_podcast
        ]
        
        print("\nConvertendo para formato de podcast...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_podcast if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão podcast: {str(e)}")
        return None

def converter_para_streaming(caminho_audio, caminho_saida):
    """Converte para formato otimizado para streaming."""
    try:
        timestamp = obter_timestamp_formatado()
        nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
        caminho_stream = os.path.join(caminho_saida, f"stream_{timestamp}_{nome_base}.ogg")
        
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-c:a', 'libvorbis',   # Codec Vorbis
            '-q:a', '6',           # Qualidade VBR
            '-ar', '48000',        # Sample rate para streaming
            '-y',                  # Sobrescreve se existir
            caminho_stream
        ]
        
        print("\nConvertendo para formato de streaming...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_stream if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão streaming: {str(e)}")
        return None

def converter_para_radio(caminho_audio, caminho_saida):
    """Converte para formato de rádio FM."""
    try:
        timestamp = obter_timestamp_formatado()
        nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
        caminho_radio = os.path.join(caminho_saida, f"radio_{timestamp}_{nome_base}.wav")
        
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-ar', '44100',        # Sample rate padrão para FM
            '-ac', '2',            # Estéreo
            '-acodec', 'pcm_s16le', # PCM 16-bit
            '-af', 'acompressor=threshold=-16dB:ratio=4,volume=2', # Compressão dinâmica
            '-y',                  # Sobrescreve se existir
            caminho_radio
        ]
        
        print("\nConvertendo para formato de rádio...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_radio if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão rádio: {str(e)}")
        return None

def converter_para_whatsapp(caminho_audio, caminho_saida):
    """Converte para formato ideal para WhatsApp."""
    try:
        timestamp = obter_timestamp_formatado()
        nome_base = os.path.splitext(os.path.basename(caminho_audio))[0]
        caminho_whatsapp = os.path.join(caminho_saida, f"whatsapp_{timestamp}_{nome_base}.ogg")
        
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-c:a', 'libopus',     # Codec Opus (usado pelo WhatsApp)
            '-b:a', '128k',        # Bitrate balanceado
            '-ar', '48000',        # Sample rate padrão para Opus
            '-af', 'volume=1.5',   # Leve aumento de volume
            '-y',                  # Sobrescreve se existir
            caminho_whatsapp
        ]
        
        print("\nConvertendo para formato do WhatsApp...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_whatsapp if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão WhatsApp: {str(e)}")
        return None

def processar_video(origem, diretorio_saida, formatos_selecionados):
    """Função principal que executa todo o processamento."""
    print("\nVerificando instalação do FFmpeg...")
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except Exception:
        print("Erro: FFmpeg ou FFprobe não está instalado ou não está acessível!")
        return None, None

    # Processamento inicial do vídeo
    if verifica_arquivo_local(origem):
        caminho_video = processar_video_local(origem, diretorio_saida)
    elif verifica_url(origem):
        caminho_video = baixar_do_youtube(origem, diretorio_saida)
    else:
        print("Erro: Fonte inválida. Forneça uma URL válida ou caminho de arquivo local.")
        return None, None

    if not caminho_video:
        return None, None
    
    # Extração do áudio base para conversões
    caminho_audio = extrair_audio(caminho_video, diretorio_saida)
    if not caminho_audio:
        return caminho_video, None

    arquivos_gerados = [caminho_video, caminho_audio]

    # Processa os formatos selecionados
    if '1' in formatos_selecionados:  # Padrão telefonia
        caminho_telefonia = converter_para_telefonia(caminho_audio, diretorio_saida)
        if caminho_telefonia:
            arquivos_gerados.append(caminho_telefonia)

    if '2' in formatos_selecionados:  # Alta Qualidade
        caminho_hq = converter_para_alta_qualidade(caminho_audio, diretorio_saida)
        if caminho_hq:
            arquivos_gerados.append(caminho_hq)

    if '3' in formatos_selecionados:  # Podcast
        caminho_podcast = converter_para_podcast(caminho_audio, diretorio_saida)
        if caminho_podcast:
            arquivos_gerados.append(caminho_podcast)

    if '4' in formatos_selecionados:  # Streaming
        caminho_stream = converter_para_streaming(caminho_audio, diretorio_saida)
        if caminho_stream:
            arquivos_gerados.append(caminho_stream)

    if '5' in formatos_selecionados:  # Rádio
        caminho_radio = converter_para_radio(caminho_audio, diretorio_saida)
        if caminho_radio:
            arquivos_gerados.append(caminho_radio)

    if '6' in formatos_selecionados:  # WhatsApp
        caminho_whatsapp = converter_para_whatsapp(caminho_audio, diretorio_saida)
        if caminho_whatsapp:
            arquivos_gerados.append(caminho_whatsapp)

    return caminho_video, arquivos_gerados

if __name__ == "__main__":
    try:
        print("\nProcessador de Vídeo e Áudio")
        print("============================")
        print("\nEste script pode processar vídeos de diferentes fontes:")
        print("1. YouTube")
        print("2. Arquivos locais")
        
        origem = input("\nDigite a URL do vídeo ou o caminho do arquivo local: ")
        
        print("\nEscolha os formatos de saída desejados:")
        print("1. Padrão Telefonia (WAV 8kHz)")
        print("2. Alta Qualidade (FLAC 96kHz)")
        print("3. Podcast (M4A)")
        print("4. Streaming (OGG)")
        print("5. Rádio FM (WAV)")
        print("6. WhatsApp (OGG/OPUS)")
        
        formatos = input("\nDigite os números dos formatos desejados (separados por vírgula): ").split(',')
        formatos = [f.strip() for f in formatos]  # Remove espaços em branco
        
        diretorio_saida = criar_diretorio_saida()
        caminho_video, arquivos_gerados = processar_video(origem, diretorio_saida, formatos)
        
        if arquivos_gerados:
            print("\nProcessamento concluído com sucesso!")
            print("\nArquivos gerados:")
            for i, caminho_arquivo in enumerate(arquivos_gerados, 1):
                print(f"{i}. {os.path.basename(caminho_arquivo)}")
        else:
            print("\nErro: Nenhum arquivo foi gerado.")
            
    except KeyboardInterrupt:
        print("\nProcessamento interrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro inesperado: {str(e)}")
    finally:
        input("\nPressione Enter para sair...")