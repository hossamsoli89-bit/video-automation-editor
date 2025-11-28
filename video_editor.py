import os
import re
import requests
import random
import sys
import traceback
import tempfile
import shutil
import logging

# إعداد نظام التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- محاولة استيراد المكتبات مع معالجة الأخطاء ---
try:
    from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
    from moviepy.video.tools.subtitles import SubtitlesClip
    from PIL import Image, ImageDraw, ImageFont
    import textwrap
    logger.info("تم استيراد جميع المكتبات بنجاح")
except ImportError as e:
    logger.error(f"خطأ في استيراد المكتبات: {e}")
    logger.error("تأكد من تثبيت جميع المكتبات المطلوبة.")
    sys.exit(1)

# --- الإعدادات ---
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

logger.info(f"PEXELS_API_KEY موجود: {'نعم' if PEXELS_API_KEY else 'لا'}")
logger.info(f"GOOGLE_DRIVE_FOLDER_ID موجود: {'نعم' if GOOGLE_DRIVE_FOLDER_ID else 'لا'}")

# --- سيناريو الفيديو ---
SCRIPT = """
أهلًا بالجميع! كيف حالكم اليوم؟ هل تشعرون بأنكم بحاجة لجرعة إضافية من السعادة؟
أنا متأكد أن الإجابة هي نعم! كلنا نبحث عن السعادة، لكن أحيانًا ننسى أنها تكمن في أبسط الأشياء.
لذلك، قررت أن أبدأ تحديًا جديدًا ومثيرًا: "30 يوم سعادة"!
فكرة بسيطة جدًا: لمدة 30 يومًا، سأشارككم تحديًا يوميًا.
تحدي اليوم الأول بسيط جدًا: ابتسم لشخص غريب! نعم، ابتسم فقط!
"""

# --- وظائف مساعدة ---

def search_pexels_videos(query, per_page=3):
    """البحث عن فيديوهات باستخدام Pexels API"""
    logger.info(f"البحث عن فيديوهات باستخدام الكلمة المفتاحية: {query}")
    
    if not PEXELS_API_KEY:
        logger.error("مفتاح Pexels API غير موجود.")
        return []
    
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={per_page}"
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        videos = data.get('videos', [])
        logger.info(f"تم العثور على {len(videos)} فيديو")
        return videos
    except requests.exceptions.RequestException as e:
        logger.error(f"خطأ في البحث في Pexels: {e}")
        return []
    except Exception as e:
        logger.error(f"خطأ غير متوقع في البحث في Pexels: {e}")
        return []

def download_video(video_data, filename):
    """تنزيل فيديو من Pexels"""
    logger.info(f"تنزيل الفيديو: {video_data.get('id')}")
    
    try:
        video_files = video_data.get('video_files', [])
        if not video_files:
            logger.warning(f"لا توجد ملفات فيديو للفيديو: {video_data.get('id')}")
            return None
        
        best_quality_file = max(video_files, key=lambda f: f.get('width', 0) * f.get('height', 0), default=None)
        
        if best_quality_file:
            video_url = best_quality_file['link']
            logger.info(f"تنزيل الفيديو من: {video_url}")
            
            try:
                response = requests.get(video_url, stream=True, timeout=60)
                response.raise_for_status()
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = os.path.getsize(filename)
                logger.info(f"تم تنزيل الفيديو بنجاح. الحجم: {file_size} bytes")
                return filename
            except Exception as e:
                logger.error(f"فشل في تنزيل الفيديو: {e}")
                return None
    except Exception as e:
        logger.error(f"خطأ غير متوقع في تنزيل الفيديو: {e}")
        return None

def create_subtitle(text, start_time, end_time, fontsize=40):
    """إنشاء كليب ترجمة فرعي"""
    def format_time(t):
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        milliseconds = int((t - int(t)) * 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    
    return f"{format_time(start_time)} --> {format_time(end_time)}\n{text}\n\n"

def create_text_clip(text, duration, fontsize=40, color='white', bgcolor='black', size=(1280, 720)):
    """إنشاء كليب نصي يعرض النص على الشاشة"""
    logger.info(f"إنشاء كليب نصي للنص: {text[:30]}...")
    
    try:
        img = Image.new('RGB', size, bgcolor)
        draw = ImageDraw.Draw(img)
        
        # محاولة استخدام خطوط متعددة
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Arial.ttf"
        ]
        
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, fontsize)
                break
            except IOError:
                continue
        
        # استخدام الخط الافتراضي إذا لم يتم العثور على خط
        if font is None:
            font = ImageFont.load_default()
            logger.warning("استخدام الخط الافتراضي لأنه لم يتم العثور على خط مناسب.")

        lines = textwrap.wrap(text, width=40)
        y_text = 10
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x_text = (size[0] - text_width) / 2
            draw.text((x_text, y_text), line, font=font, fill=color)
            y_text += text_height + 10

        txt_clip = ImageClip(img)
        txt_clip = txt_clip.set_duration(duration)
        return txt_clip
    except Exception as e:
        logger.error(f"خطأ في إنشاء كليب نصي: {e}")
        return None

# --- المنطق الرئيسي ---

def main():
    logger.info("بدء عملية إنشاء الفيديو...")
    
    # إنشاء دليل مؤقت
    temp_dir = tempfile.mkdtemp()
    logger.info(f"تم إنشاء دليل مؤقت: {temp_dir}")
    
    try:
        # تقسيم السيناريو إلى جمل
        sentences = re.split(r'(?<=[.!?])\s+', SCRIPT.strip())
        logger.info(f"تم تقسيم السيناريو إلى {len(sentences)} جملة للبحث.")

        video_clips = []
        current_time = 0
        subtitles = ""
        
        # معالجة كل جملة
        for i, sentence in enumerate(sentences):
            logger.info(f"معالجة الجملة {i+1}: '{sentence[:30]}...'")
            
            # اختيار كلمة مفتاحية للبحث
            keywords = [word for word in sentence.split() if len(word) > 4]
            query = random.choice(keywords) if keywords else "happy people"
            
            logger.info(f"البحث عن فيديوهات باستخدام الكلمة المفتا
