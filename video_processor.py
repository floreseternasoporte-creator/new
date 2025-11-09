import os
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from deep_translator import GoogleTranslator
import torch
import logging
import boto3

logger = logging.getLogger(__name__)

# Configurar credenciales AWS desde variables de entorno
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')
S3_BUCKET = os.getenv('S3_BUCKET', 'll-ai-models-240032')

class VideoProcessor:
    def __init__(self):
        logger.info("🔄 Inicializando VideoProcessor...")
        self.s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)
        
        logger.info("📥 Descargando modelo Whisper desde S3...")
        whisper_cache = os.path.expanduser("~/.cache/whisper")
        os.makedirs(whisper_cache, exist_ok=True)
        whisper_model_path = f"{whisper_cache}/base.pt"
        if not os.path.exists(whisper_model_path):
            self.s3.download_file(S3_BUCKET, 'whisper/base.pt', whisper_model_path)
            logger.info("✅ Modelo Whisper descargado desde S3")
        
        self.whisper_model = whisper.load_model("base")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"✅ Dispositivo: {self.device}")
        
        self._init_tts()
    
    def _init_tts(self):
        """Inicializa el modelo TTS para clonación de voz"""
        try:
            logger.info("📥 Descargando XTTS v2 desde S3...")
            os.environ['COQUI_TOS_AGREED'] = '1'
            
            tts_cache = os.path.expanduser("~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2")
            os.makedirs(tts_cache, exist_ok=True)
            
            model_path = f"{tts_cache}/model.pth"
            speakers_path = f"{tts_cache}/speakers_xtts.pth"
            
            if not os.path.exists(model_path):
                logger.info("📥 Descargando model.pth...")
                self.s3.download_file(S3_BUCKET, 'tts/tts_models--multilingual--multi-dataset--xtts_v2/model.pth', model_path)
            if not os.path.exists(speakers_path):
                logger.info("📥 Descargando speakers_xtts.pth...")
                self.s3.download_file(S3_BUCKET, 'tts/tts_models--multilingual--multi-dataset--xtts_v2/speakers_xtts.pth', speakers_path)
            
            logger.info("✅ Modelos descargados desde S3")
            from TTS.api import TTS
            self.tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(self.device)
            logger.info("✅ XTTS v2 cargado - Clonación de voz ACTIVA")
            self.use_voice_cloning = True
        except Exception as e:
            logger.warning(f"⚠️  XTTS v2 no disponible: {e}")
            logger.info("📥 Usando gTTS como alternativa...")
            self.tts_model = None
            self.use_voice_cloning = False
    
    def extract_audio(self, video_path, audio_path):
        """Extrae el audio del video"""
        logger.info(f"🎵 Extrayendo audio de {video_path}")
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path, codec='pcm_s16le', logger=None)
        video.close()
        logger.info(f"✅ Audio extraído: {audio_path}")
        return audio_path
    
    def transcribe_audio(self, audio_path):
        """Transcribe el audio usando Whisper"""
        logger.info(f"📝 Transcribiendo audio...")
        result = self.whisper_model.transcribe(audio_path)
        text = result["text"]
        lang = result.get("language", "en")
        logger.info(f"✅ Transcripción completa. Idioma detectado: {lang}")
        logger.info(f"📄 Texto: {text[:100]}...")
        return text, lang
    
    def translate_text(self, text, source_lang, target_lang):
        """Traduce el texto al idioma objetivo"""
        logger.info(f"🌐 Traduciendo de {source_lang} a {target_lang}...")
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(text)
        logger.info(f"✅ Traducción completa")
        logger.info(f"📄 Texto traducido: {translated[:100]}...")
        return translated
    
    def generate_voice(self, text, target_lang, reference_audio, output_path):
        """Genera audio con voz clonada o TTS estándar"""
        if self.use_voice_cloning and self.tts_model is not None:
            try:
                logger.info("🎤 Generando audio con CLONACIÓN DE VOZ...")
                self.tts_model.tts_to_file(
                    text=text,
                    speaker_wav=reference_audio,
                    language=target_lang,
                    file_path=output_path
                )
                logger.info("✅ Audio generado con voz clonada")
                return output_path
            except Exception as e:
                logger.error(f"❌ Error en clonación de voz: {e}")
                logger.info("🔄 Intentando con gTTS...")
        
        # Fallback a gTTS
        logger.info("🎤 Generando audio con gTTS...")
        from gtts import gTTS
        lang_map = {"zh-CN": "zh-cn", "zh": "zh-cn"}
        lang = lang_map.get(target_lang, target_lang)
        tts_obj = gTTS(text=text, lang=lang, slow=False)
        tts_obj.save(output_path)
        logger.info("✅ Audio generado con gTTS")
        return output_path
    
    def replace_audio(self, video_path, new_audio_path, output_path):
        """Reemplaza el audio del video"""
        logger.info("🎬 Reemplazando audio en video...")
        video = VideoFileClip(video_path)
        new_audio = AudioFileClip(new_audio_path)
        
        if new_audio.duration > video.duration:
            new_audio = new_audio.subclipped(0, video.duration)
        
        video.audio = new_audio
        video.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None)
        
        video.close()
        new_audio.close()
        logger.info(f"✅ Video final creado: {output_path}")
        return output_path
    
    def process_video(self, video_path, target_lang, output_path):
        """Procesa el video completo: extrae audio, transcribe, traduce y genera nuevo video"""
        temp_audio = video_path.replace(".mp4", "_audio.wav")
        translated_audio = video_path.replace(".mp4", "_translated.wav")
        
        try:
            logger.info("=" * 60)
            logger.info("🚀 INICIANDO PROCESAMIENTO DE VIDEO")
            logger.info("=" * 60)
            
            # 1. Extraer audio
            self.extract_audio(video_path, temp_audio)
            
            # 2. Transcribir
            text, source_lang = self.transcribe_audio(temp_audio)
            
            # 3. Traducir
            translated_text = self.translate_text(text, source_lang, target_lang)
            
            # 4. Generar voz clonada
            self.generate_voice(translated_text, target_lang, temp_audio, translated_audio)
            
            # 5. Reemplazar audio en video
            self.replace_audio(video_path, translated_audio, output_path)
            
            logger.info("=" * 60)
            logger.info("✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
            logger.info("=" * 60)
            
            return output_path, text, translated_text
        
        except Exception as e:
            logger.error(f"❌ ERROR EN PROCESAMIENTO: {e}", exc_info=True)
            raise
        
        finally:
            # Limpiar archivos temporales
            for f in [temp_audio, translated_audio]:
                if os.path.exists(f):
                    os.remove(f)
                    logger.info(f"🗑️  Archivo temporal eliminado: {f}")
