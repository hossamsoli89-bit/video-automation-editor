import os
import json
import logging
from uploaders import VideoUploader

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # التحقق من وجود الفيديو
        video_path = "final_video.mp4"
        if not os.path.exists(video_path):
            logger.error(f"الفيديو غير موجود: {video_path}")
            return False
        
        # إنشاء عنوان ديناميكي
        from datetime import datetime
        title = f"فيديو تلقائي - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        description = "فيديو تم إنشاؤه تلقائيًا باستخدام Python و GitHub Actions"
        
        # رفع الفيديو
        uploader = VideoUploader()
        results = uploader.upload_to_all(video_path, title, description)
        
        # طباعة النتائج
        logger.info("=== النتائج النهائية ===")
        logger.info(f"YouTube: https://youtube.com/watch?v={results['youtube_id']}")
        logger.info(f"TikTok: {'نجح' if results['tiktok_success'] else 'فشل'}")
        
        return True
        
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
