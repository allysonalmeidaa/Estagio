
import whisper
import os

print("Diretório atual:", os.getcwd())
print("Arquivos:", os.listdir())
    
    
modelo = whisper.load_model("medium")
resultado = modelo.transcribe("reunião.mp4")
    
print(resultado["text"])

