import os
import logging
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import TELEGRAM_TOKEN, SUPPORTED_LANGUAGES, TEMP_DIR, MAX_VIDEO_SIZE
from video_processor import VideoProcessor

# Configurar logging detallado
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Crear directorio temporal
os.makedirs(TEMP_DIR, exist_ok=True)
logger.info(f"📁 Directorio temporal creado: {TEMP_DIR}")

# Inicializar procesador de video
logger.info("🤖 Inicializando Bot de Traducción de Videos...")
try:
    processor = VideoProcessor()
    logger.info("✅ VideoProcessor inicializado correctamente")
except Exception as e:
    logger.error(f"❌ Error inicializando VideoProcessor: {e}", exc_info=True)
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    logger.info(f"👤 Usuario {user.id} ({user.username}) ejecutó /start")
    
    await update.message.reply_text(
        "🎬 *Bot de Traducción de Videos con Clonación de Voz*\n\n"
        "¡Bienvenido! Puedo traducir tus videos manteniendo la voz original.\n\n"
        "📤 Envíame un video para comenzar\n"
        "❓ Usa /help para más información\n"
        "📊 Usa /stats para ver estadísticas",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    logger.info(f"👤 Usuario {update.effective_user.id} ejecutó /help")
    
    await update.message.reply_text(
        "📖 *Guía de Uso*\n\n"
        "*Paso 1:* Envía un video (máx. 50 MB)\n"
        "*Paso 2:* Selecciona el idioma de destino\n"
        "*Paso 3:* Espera el procesamiento (puede tomar varios minutos)\n"
        "*Paso 4:* Recibe tu video traducido con voz clonada\n\n"
        "*🌍 Idiomas soportados:*\n"
        + "\n".join([f"• {name}" for name in SUPPORTED_LANGUAGES.values()]) +
        "\n\n*⚙️ Características:*\n"
        "✅ Clonación de voz en tiempo real\n"
        "✅ Transcripción automática con IA\n"
        "✅ Traducción a 9 idiomas\n"
        "✅ Sincronización perfecta de audio",
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats"""
    logger.info(f"👤 Usuario {update.effective_user.id} ejecutó /stats")
    
    stats_text = (
        "📊 *Estadísticas del Bot*\n\n"
        f"🤖 Estado: ✅ Activo 24/7\n"
        f"🎤 Clonación de voz: {'✅ Activa' if processor.use_voice_cloning else '⚠️ Desactivada'}\n"
        f"💻 Dispositivo: {processor.device.upper()}\n"
        f"📁 Directorio temporal: {TEMP_DIR}\n"
        f"⏰ Hora del servidor: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja videos recibidos"""
    user = update.effective_user
    video = update.message.video
    
    logger.info(f"📹 Video recibido de usuario {user.id} ({user.username})")
    logger.info(f"   Tamaño: {video.file_size / (1024*1024):.2f} MB")
    logger.info(f"   Duración: {video.duration}s")
    
    if video.file_size > MAX_VIDEO_SIZE:
        logger.warning(f"⚠️  Video demasiado grande: {video.file_size / (1024*1024):.2f} MB")
        await update.message.reply_text(
            f"❌ El video es demasiado grande.\n"
            f"Tamaño máximo: 50 MB\n"
            f"Tu video: {video.file_size / (1024*1024):.2f} MB"
        )
        return
    
    # Guardar información del video en contexto
    context.user_data['video_file_id'] = video.file_id
    context.user_data['video_size'] = video.file_size
    context.user_data['video_duration'] = video.duration
    
    # Mostrar teclado de idiomas
    keyboard = []
    for code, name in SUPPORTED_LANGUAGES.items():
        keyboard.append([InlineKeyboardButton(name, callback_data=f"lang_{code}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌍 *Selecciona el idioma de destino:*\n\n"
        "El video será traducido manteniendo tu voz original.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    logger.info(f"✅ Teclado de idiomas mostrado al usuario {user.id}")

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección de idioma"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    target_lang = query.data.replace("lang_", "")
    video_file_id = context.user_data.get('video_file_id')
    
    logger.info(f"🌐 Usuario {user.id} seleccionó idioma: {SUPPORTED_LANGUAGES[target_lang]}")
    
    if not video_file_id:
        logger.error(f"❌ No se encontró video para usuario {user.id}")
        await query.edit_message_text("❌ Error: No se encontró el video. Envíalo nuevamente.")
        return
    
    await query.edit_message_text(
        f"⏳ *Procesando video a {SUPPORTED_LANGUAGES[target_lang]}...*\n\n"
        "🎤 Clonando tu voz...\n"
        "📝 Transcribiendo audio...\n"
        "🌐 Traduciendo texto...\n"
        "🎬 Generando video final...\n\n"
        "⏱️ Esto puede tomar varios minutos.\n"
        "Por favor espera...",
        parse_mode='Markdown'
    )
    
    video_path = None
    output_path = None
    
    try:
        # Descargar video
        logger.info(f"📥 Descargando video del usuario {user.id}...")
        file = await context.bot.get_file(video_file_id)
        video_path = os.path.join(TEMP_DIR, f"{user.id}_{datetime.now().timestamp()}_input.mp4")
        output_path = video_path.replace("_input.mp4", "_output.mp4")
        
        await file.download_to_drive(video_path)
        logger.info(f"✅ Video descargado: {video_path}")
        
        # Procesar video
        logger.info(f"🚀 Iniciando procesamiento para usuario {user.id}")
        result_path, original_text, translated_text = processor.process_video(
            video_path, target_lang, output_path
        )
        
        # Enviar video traducido
        logger.info(f"📤 Enviando video traducido al usuario {user.id}...")
        with open(result_path, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"✅ *Video traducido a {SUPPORTED_LANGUAGES[target_lang]}*\n\n"
                        f"🎤 Voz clonada: {'Sí' if processor.use_voice_cloning else 'No'}",
                parse_mode='Markdown'
            )
        logger.info(f"✅ Video enviado exitosamente al usuario {user.id}")
        
        # Enviar transcripciones
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📝 *Texto original:*\n{original_text[:500]}{'...' if len(original_text) > 500 else ''}\n\n"
                 f"🌐 *Texto traducido:*\n{translated_text[:500]}{'...' if len(translated_text) > 500 else ''}",
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Proceso completado para usuario {user.id}")
        
    except Exception as e:
        logger.error(f"❌ Error procesando video del usuario {user.id}: {e}", exc_info=True)
        error_msg = str(e).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Error al procesar el video\n\n"
                 f"Detalles: {error_msg[:200]}\n\n"
                 f"Por favor intenta nuevamente."
        )
    
    finally:
        # Limpiar archivos
        for f in [video_path, output_path]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                    logger.info(f"🗑️  Archivo eliminado: {f}")
                except Exception as e:
                    logger.error(f"⚠️  Error eliminando archivo {f}: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores globales"""
    logger.error(f"❌ Error global: {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Ocurrió un error inesperado. Por favor intenta nuevamente."
        )

def main():
    """Inicia el bot en modo 24/7"""
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO BOT DE TRADUCCIÓN DE VIDEOS 24/7")
    logger.info("=" * 60)
    logger.info(f"🔑 Token: {TELEGRAM_TOKEN[:10]}...")
    logger.info(f"🌍 Idiomas soportados: {len(SUPPORTED_LANGUAGES)}")
    logger.info(f"📁 Directorio temporal: {TEMP_DIR}")
    logger.info(f"📦 Tamaño máximo de video: {MAX_VIDEO_SIZE / (1024*1024)} MB")
    
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Agregar handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(MessageHandler(filters.VIDEO, handle_video))
        application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
        
        # Agregar error handler
        application.add_error_handler(error_handler)
        
        logger.info("✅ Handlers configurados correctamente")
        logger.info("🤖 Bot iniciado y escuchando mensajes...")
        logger.info("🔄 Modo 24/7 ACTIVO - Presiona Ctrl+C para detener")
        logger.info("=" * 60)
        
        # Ejecutar bot en modo polling (24/7)
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("⏹️  Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
