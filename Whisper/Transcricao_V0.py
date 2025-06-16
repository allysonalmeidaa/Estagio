import whisper
import os

# Caminho da pasta onde está o script
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))

# Modelos disponíveis
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

# Lista somente arquivos de áudio/vídeo da pasta do script
extensoes_validas = (".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac")
arquivos_disponiveis = [arq for arq in os.listdir(PASTA_SCRIPT) if arq.lower().endswith(extensoes_validas)]

if not arquivos_disponiveis:
    print("Nenhum arquivo de áudio ou vídeo suportado encontrado na pasta do script.")
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

# Caminho absoluto do arquivo escolhido
caminho_arquivo = os.path.join(PASTA_SCRIPT, arquivo_escolhido)

# Carrega o modelo escolhido
modelo = whisper.load_model(modelo_escolhido)

# Transcrição original
resultado = modelo.transcribe(caminho_arquivo)
print("\nTranscrição original:")
print(resultado["text"])

# Salva a transcrição original na pasta do script
caminho_transcr = os.path.join(PASTA_SCRIPT, "transcricao_original.txt")
with open(caminho_transcr, "w", encoding="utf-8") as f:
    f.write(resultado["text"])

# Tradução para o inglês
resultado_traduzido = modelo.transcribe(caminho_arquivo, task="translate")
print("\nTradução para o inglês:")
print(resultado_traduzido["text"])

# Salva a tradução para o inglês na pasta do script
caminho_trad = os.path.join(PASTA_SCRIPT, "transcricao_ingles.txt")
with open(caminho_trad, "w", encoding="utf-8") as f:
    f.write(resultado_traduzido["text"])

print("\nTranscrições salvas na pasta do script como 'transcricao_original.txt' e 'transcricao_ingles.txt'.")