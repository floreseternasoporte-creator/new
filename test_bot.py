#!/usr/bin/env python3
"""Script de prueba para verificar que todo funciona"""

print("🔍 Verificando componentes del bot...\n")

# 1. Verificar imports
print("1️⃣ Verificando imports...")
try:
    import telegram
    print("   ✅ python-telegram-bot")
except Exception as e:
    print(f"   ❌ python-telegram-bot: {e}")

try:
    import whisper
    print("   ✅ whisper")
except Exception as e:
    print(f"   ❌ whisper: {e}")

try:
    from TTS.api import TTS
    print("   ✅ TTS")
except Exception as e:
    print(f"   ❌ TTS: {e}")

try:
    import ffmpeg
    print("   ✅ ffmpeg-python")
except Exception as e:
    print(f"   ❌ ffmpeg-python: {e}")

# 2. Verificar config
print("\n2️⃣ Verificando configuración...")
try:
    from config import TELEGRAM_TOKEN, LANGUAGES
    if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "TU_TOKEN_AQUI":
        print("   ✅ Token configurado")
    else:
        print("   ❌ Token no configurado en config.py")
    print(f"   ✅ {len(LANGUAGES)} idiomas configurados")
except Exception as e:
    print(f"   ❌ Error en config: {e}")

# 3. Verificar directorios
print("\n3️⃣ Verificando directorios...")
import os
if os.path.exists("temp"):
    print("   ✅ Directorio temp existe")
else:
    print("   ❌ Directorio temp no existe")
    os.makedirs("temp")
    print("   ✅ Directorio temp creado")

# 4. Verificar modelos
print("\n4️⃣ Verificando modelos...")
try:
    print("   Cargando Whisper base...")
    model = whisper.load_model("base")
    print("   ✅ Whisper base cargado")
except Exception as e:
    print(f"   ❌ Error cargando Whisper: {e}")

try:
    print("   Cargando TTS...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    print("   ✅ TTS cargado")
except Exception as e:
    print(f"   ❌ Error cargando TTS: {e}")

print("\n✅ Verificación completada!")
