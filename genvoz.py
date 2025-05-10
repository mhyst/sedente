from gtts import gTTS
import os

tts = gTTS("Tómate una pausa y no olvides estirar las piernas", lang='es')
tts.save("voz.mp3")
