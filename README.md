# Bot de Traducción de Videos para Telegram

Bot que traduce videos manteniendo la voz original usando clonación de voz.

## 🚀 Instalación

```bash
# Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install ffmpeg

# Instalar dependencias de Python
pip install -r requirements.txt
```

## ▶️ Ejecutar el bot

```bash
python bot.py
```

## 📋 Funcionalidades

- ✅ Extracción de audio del video
- ✅ Transcripción automática con Whisper
- ✅ Traducción a múltiples idiomas
- ✅ Clonación de voz con TTS
- ✅ Sincronización de audio con video
- ✅ Interfaz interactiva en Telegram

## 🌍 Idiomas soportados

- Español
- English
- Français
- Deutsch
- Italiano
- Português
- Русский
- 日本語
- 中文

## 📝 Uso

1. Inicia el bot con `/start`
2. Envía un video (máx. 50 MB)
3. Selecciona el idioma de destino
4. Espera el procesamiento
5. Recibe tu video traducido

## ⚙️ Configuración

Edita `config.py` para cambiar:
- Token de Telegram
- Idiomas soportados
- Tamaño máximo de video
- Directorio temporal

## 🔧 Requisitos del sistema

- Python 3.10+
- FFmpeg
- 4GB RAM mínimo (8GB recomendado)
- GPU opcional (acelera el procesamiento)
