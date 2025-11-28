import os
import sys
import tempfile
import shutil
import logging
from PIL import Image, ImageDraw, ImageFont

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from moviepy.editor import ImageClip, concatenate_videoclips, CompositeVideoClip, TextClip
    logger.info("تم استيراد moviepy بنجاح")
except ImportError as e:
    logger.error(f"خطأ في استيراد moviepy: {e}")
    sys.exit(1)

def create_simple_video():
    """إنشاء فيديو بسيط بدون الاعتماد على API خارجي"""
    logger.info("بدء إنشاء فيديو بسيط...")
    
    # إنشاء دليل مؤقت
    temp_dir = tempfile.mkdtemp()
    logger.info(f"تم إنشاء دليل مؤقت: {temp_dir}")
    
    try:
        # إنشاء صورة نصية
        img_path = os.path.join(temp_dir, "text_image.png")
        img = Image.new('RGB', (1280, 720), color='black')
        draw = ImageDraw.Draw(img)
        
        # استخدام خط افتراضي
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # كتابة النص
        text = "فيديو تجريبي\nتم إنشاؤه بنجاح!"
        lines = text.split('\n')
        y_text = 200
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x_text = (1280 - text_width) / 2
            draw.text((x_text, y_text), line, font=font, fill='white')
            y_text += text_height + 20
        
        img.save(img_path)
        logger.info("تم إنشاء الصورة النصية")
        
        # إنشاء كليب من الصورة
        clip = ImageClip(img_path)
        clip = clip.set_duration(5)
        
        # إضافة نص متحرك
        try:
            txt_clip = TextClip(
                "Hello World!", 
                fontsize=70, 
                color='white',
                bg_color='transparent'
            ).set_position('center').set_duration(5)
            
            final_clip = CompositeVideoClip([clip, txt_clip])
        except:
            # إذا فشل TextClip، استخدم الصورة فقط
            final_clip = clip
        
        # حفظ الفيديو
        output_path = os.path.join(temp_dir, "simple_video.mp4")
        logger.info(f"حفظ الفيديو في: {output_path}")
        
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            verbose=False,
            logger=None
        )
        
        # نسخ الفيديو إلى المجلد الرئيسي
        final_output = os.path.join(os.getcwd(), "final_video.mp4")
        shutil.copy2(output_path, final_output)
        
        # التحقق من وجود الملف
        if os.path.exists(final_output):
            size = os.path.getsize(final_output)
            logger.info(f"تم إنشاء الفيديو بنجاح! الحجم: {size} bytes")
            return True
        else:
            logger.error("لم يتم العثور على الفيديو النهائي")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إنشاء الفيديو: {e}")
        return False
    finally:
        # تنظيف الملفات المؤقتة
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info("تم تنظيف الملفات المؤقتة")

if __name__ == "__main__":
    try:
        success = create_simple_video()
        if success:
            logger.info("اكتمل التنفيذ بنجاح")
            sys.exit(0)
        else:
            logger.error("فشل في
