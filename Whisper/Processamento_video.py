import os
import subprocess
import yt_dlp
from datetime import datetime

def criar_diretorio_saida():
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    diretorio_saida = os.path.join(diretorio_script, "saida_audio")
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)
    return diretorio_saida

def verifica_arquivo_local(caminho):
    caminho = caminho.strip('"\'')
    return os.path.isfile(caminho)

def verifica_url(texto):
    return texto.strip('"\'').startswith(('http://', 'https://', 'www.'))

def nome_base_entrada(origem):
    # Sempre pega o nome do arquivo original, mesmo se for URL
    if os.path.isfile(origem):
        return os.path.splitext(os.path.basename(origem))[0]
    elif verifica_url(origem):
        # Se for URL do YouTube, tenta extrair o nome a partir do título após download
        # Mas para garantir, você pode usar um identificador temporário ou tratar no download
        return None  # Será definido após o download no fluxo principal
    else:
        return "arquivo"

def processar_video_local(caminho_origem, caminho_saida, nome_base):
    try:
        caminho_origem = caminho_origem.strip('"\'')
        if not os.path.exists(caminho_origem):
            print(f"Erro: Arquivo não encontrado: {caminho_origem}")
            return None

        destino = os.path.join(caminho_saida, f"video_{nome_base}.mp4")

        print(f"\nProcessando arquivo local: {caminho_origem}")
        print(f"Para: {destino}")

        comando = [
            'ffmpeg',
            '-i', caminho_origem,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y',
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
    try:
        opcoes_ydl = {
            'format': 'best',
            'outtmpl': os.path.join(caminho_saida, f"video_%(title)s.%(ext)s"),
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
            # Renomeia para garantir que fica video_nomeoriginal.mp4
            titulo = info.get('title') or 'youtube'
            nome_base = titulo.replace(" ", "_")
            caminho_final = os.path.join(os.path.dirname(caminho_video), f"video_{nome_base}.mp4")
            if caminho_video != caminho_final:
                os.rename(caminho_video, caminho_final)
            return caminho_final, nome_base
    except Exception as e:
        print(f"Erro ao baixar do YouTube: {str(e)}")
        return None, None

def extrair_audio(caminho_video, caminho_saida, nome_base):
    try:
        caminho_audio = os.path.join(caminho_saida, f"audio_{nome_base}.mp3")
        comando = [
            'ffmpeg',
            '-i', caminho_video,
            '-vn',
            '-acodec', 'libmp3lame',
            '-ab', '192k',
            '-ar', '44100',
            '-af', 'volume=2.0',
            '-y',
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

def converter_para_telefonia(caminho_audio, caminho_saida, nome_base):
    try:
        caminho_telefonia = os.path.join(caminho_saida, f"telefonia_{nome_base}.wav")
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-ar', '8000',
            '-ac', '1',
            '-acodec', 'pcm_s16le',
            '-af', 'volume=3.0,highpass=f=300,lowpass=f=3400',
            '-y',
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

def converter_para_alta_qualidade(caminho_audio, caminho_saida, nome_base):
    try:
        caminho_hq = os.path.join(caminho_saida, f"hq_{nome_base}.flac")
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-c:a', 'flac',
            '-ar', '96000',
            '-bits_per_raw_sample', '24',
            '-y',
            caminho_hq
        ]
        
        print("\nConvertendo para formato de alta qualidade (FLAC)...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_hq if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão HQ: {str(e)}")
        return None

def converter_para_podcast(caminho_audio, caminho_saida, nome_base):
    try:
        caminho_podcast = os.path.join(caminho_saida, f"podcast_{nome_base}.m4a")
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '44100',
            '-af', 'loudnorm',
            '-y',
            caminho_podcast
        ]
        print("\nConvertendo para formato de podcast...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_podcast if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão podcast: {str(e)}")
        return None

def converter_para_streaming(caminho_audio, caminho_saida, nome_base):
    try:
        caminho_stream = os.path.join(caminho_saida, f"stream_{nome_base}.ogg")
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-c:a', 'libvorbis',
            '-q:a', '6',
            '-ar', '48000',
            '-y',
            caminho_stream
        ]
        print("\nConvertendo para formato de streaming...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_stream if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão streaming: {str(e)}")
        return None

def converter_para_radio(caminho_audio, caminho_saida, nome_base):
    try:
        caminho_radio = os.path.join(caminho_saida, f"radio_{nome_base}.wav")
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-ar', '44100',
            '-ac', '2',
            '-acodec', 'pcm_s16le',
            '-af', 'acompressor=threshold=-16dB:ratio=4,volume=2',
            '-y',
            caminho_radio
        ]
        print("\nConvertendo para formato de rádio...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_radio if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão rádio: {str(e)}")
        return None

def converter_para_whatsapp(caminho_audio, caminho_saida, nome_base):
    try:
        caminho_whatsapp = os.path.join(caminho_saida, f"whatsapp_{nome_base}.ogg")
        comando = [
            'ffmpeg',
            '-i', caminho_audio,
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-ar', '48000',
            '-af', 'volume=1.5',
            '-y',
            caminho_whatsapp
        ]
        print("\nConvertendo para formato do WhatsApp...")
        processo = subprocess.run(comando, capture_output=True, text=True)
        return caminho_whatsapp if processo.returncode == 0 else None
    except Exception as e:
        print(f"Erro na conversão WhatsApp: {str(e)}")
        return None

def processar_video(origem, diretorio_saida, formatos_selecionados):
    print("\nVerificando instalação do FFmpeg...")
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except Exception:
        print("Erro: FFmpeg ou FFprobe não está instalado ou não está acessível!")
        return None, None

    if verifica_arquivo_local(origem):
        nome_base = nome_base_entrada(origem)
        caminho_video = processar_video_local(origem, diretorio_saida, nome_base)
    elif verifica_url(origem):
        caminho_video, nome_base = baixar_do_youtube(origem, diretorio_saida)
        if not nome_base:
            nome_base = "video"
    else:
        print("Erro: Fonte inválida. Forneça uma URL válida ou caminho de arquivo local.")
        return None, None

    if not caminho_video:
        return None, None

    caminho_audio = extrair_audio(caminho_video, diretorio_saida, nome_base)
    if not caminho_audio:
        return caminho_video, None

    arquivos_gerados = [caminho_video, caminho_audio]

    if '1' in formatos_selecionados:
        caminho_telefonia = converter_para_telefonia(caminho_audio, diretorio_saida, nome_base)
        if caminho_telefonia:
            arquivos_gerados.append(caminho_telefonia)
    if '2' in formatos_selecionados:
        caminho_hq = converter_para_alta_qualidade(caminho_audio, diretorio_saida, nome_base)
        if caminho_hq:
            arquivos_gerados.append(caminho_hq)
    if '3' in formatos_selecionados:
        caminho_podcast = converter_para_podcast(caminho_audio, diretorio_saida, nome_base)
        if caminho_podcast:
            arquivos_gerados.append(caminho_podcast)
    if '4' in formatos_selecionados:
        caminho_stream = converter_para_streaming(caminho_audio, diretorio_saida, nome_base)
        if caminho_stream:
            arquivos_gerados.append(caminho_stream)
    if '5' in formatos_selecionados:
        caminho_radio = converter_para_radio(caminho_audio, diretorio_saida, nome_base)
        if caminho_radio:
            arquivos_gerados.append(caminho_radio)
    if '6' in formatos_selecionados:
        caminho_whatsapp = converter_para_whatsapp(caminho_audio, diretorio_saida, nome_base)
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
        formatos = [f.strip() for f in formatos]
        
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