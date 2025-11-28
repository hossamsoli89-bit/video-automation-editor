import os
import sys
import subprocess
import tempfile
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_video_with_ffmpeg():
    """إنشاء فيديو باستخدام ffmpeg مباشرة"""
    logger.info("بدء إنشاء فيديو باستخدام ffmpeg...")
    
    # إنشاء دليل مؤقت
    temp_dir = tempfile.mkdtemp()
    logger.info(f"تم إنشاء دليل مؤقت: {temp_dir}")
    
    try:
        # إنشاء صورة نصية باستخدام ImageMagick
        img_path = os.path.join(temp_dir, "text.png")
        cmd = [
            "convert",
            "-size", "1280x720",
            "xc:black",
            "-font", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "-pointsize", "60",
            "-fill", "white",
            "-gravity", "center",
            "-annotate", "+0+0",
            "فيديو تجريبي\nتم إنشاؤه بنجاح!",
            img_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"فشل في إنشاء الصورة: {result.stderr}")
            return False
        
        logger.info("تم إنشاء الصورة النصية")
        
        # إنشاء فيديو باستخدام ffmpeg
        output_path = os.path.join(temp_dir, "output.mp4")
        cmd = [
            "ffmpeg",
            "-loop", "1",
            "-i", img_path,
            "-c:v", "libx264",
            "-t", "5",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1280:720",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"فشل في إنشاء الفيديو: {result.stderr}")
            return False
        
        logger.info("تم إنشاء الفيديو بنجاح")
        
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
        success = create_video_with_ffmpeg()
        if success:
            logger.info("اكتمل التنفيذ بنجاح")
            sys.exit(0)
        else:
            logger.error("فشل في إنشاء الفيديو")
            sys.exit(1)
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        sys.exit(1)
