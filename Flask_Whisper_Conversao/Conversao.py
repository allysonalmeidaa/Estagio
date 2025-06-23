from pydub import AudioSegment
import os

def converter_audio(input_path, output_path, formato_saida):
    ext = input_path.rsplit('.', 1)[-1].lower()
    audio = AudioSegment.from_file(input_path, format=ext)
    audio.export(output_path, format=formato_saida)
    return output_path

def baixar_youtube(link, pasta_destino):
    import yt_dlp
    ydl_opts = {
        'outtmpl': os.path.join(pasta_destino, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        downloaded_path = ydl.prepare_filename(info)
        filename = os.path.basename(downloaded_path)
        return filename, downloaded_path