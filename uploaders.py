import os
import json
import time
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self):
        self.service_account_key = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
        if not self.service_account_key:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY not found in environment variables")
        
        self.credentials = service_account.Credentials.from_service_account_info(
            json.loads(self.service_account_key),
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
    
    def upload_video(self, video_path, title="فيديو تلقائي", description="تم إنشاؤه تلقائيًا", tags=None, privacy="public"):
        """رفع فيديو إلى YouTube"""
        try:
            logger.info(f"بدء رفع الفيديو: {video_path}")
            
            # إعداد الطلب
            request_body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or ['تلقائي', 'بايثون', 'سعادة'],
                    'categoryId': '22'  # Entertainment
                },
                'status': {
                    'privacyStatus': privacy
                }
            }
            
            # رفع الفيديو
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"تم رفع {int(status.progress() * 100)}%")
            
            video_id = response['id']
            logger.info(f"✅ تم رفع الفيديو بنجاح! ID: {video_id}")
            return video_id
            
        except Exception as e:
            logger.error(f"❌ خطأ في رفع الفيديو: {e}")
            return None

class TikTokUploader:
    def __init__(self):
        self.setup_driver()
    
    def setup_driver(self):
        """إعداد متصفح Chrome"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ تم إعداد المتصفح بنجاح")
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد المتصفح: {e}")
            raise
    
    def upload_video(self, video_path, title="فيديو تلقائي", description="تم إنشاؤه تلقائيًا"):
        """رفع فيديو إلى TikTok"""
        try:
            logger.info(f"بدء رفع الفيديو إلى TikTok: {video_path}")
            
            # فتح صفحة رفع TikTok
            self.driver.get('https://www.tiktok.com/upload')
            time.sleep(5)
            
            # رفع الفيديو
            upload_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
            )
            upload_input.send_keys(os.path.abspath(video_path))
            logger.info("✅ تم اختيار ملف الفيديو")
            
            # انتظار تحميل الفيديو
            time.sleep(10)
            
            # إضافة العنوان
            try:
                title_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//textarea'))
                )
                title_input.clear()
                title_input.send_keys(title)
                logger.info("✅ تم إضافة العنوان")
            except:
                logger.warning("⚠️ لم يتم العثور على حقل العنوان")
            
            # إضافة الوصف
            try:
                desc_input = self.driver.find_element(By.XPATH, '//div[@contenteditable="true"]')
                desc_input.send_keys(description)
                logger.info("✅ تم إضافة الوصف")
            except:
                logger.warning("⚠️ لم يتم العثور على حقل الوصف")
            
            # نشر الفيديو
            try:
                post_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Post")]'))
                )
                post_button.click()
                logger.info("✅ تم النقر على زر النشر")
                time.sleep(5)
                
                # التحقق من النجاح
                if "upload" not in self.driver.current_url:
                    logger.info("✅ تم رفع الفيديو بنجاح إلى TikTok")
                    return True
                else:
                    logger.warning("⚠️ قد لا يتم رفع الفيديو بنجاح")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ خطأ في النقر على زر النشر: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في رفع الفيديو إلى TikTok: {e}")
            return False
        finally:
            self.driver.quit()
    
    def __del__(self):
        try:
            self.driver.quit()
        except:
            pass

class VideoUploader:
    def __init__(self):
        self.youtube_uploader = YouTubeUploader()
        self.tiktok_uploader = TikTokUploader()
    
    def upload_to_all(self, video_path, title="فيديو تلقائي", description="تم إنشاؤه تلقائيًا"):
        """رفع الفيديو إلى جميع المنصات"""
        results = {
            'video_path': video_path,
            'title': title,
            'description': description,
            'youtube_id': None,
            'tiktok_success': False
        }
        
        # رفع إلى YouTube
        logger.info("=== بدء رفع الفيديو إلى YouTube ===")
        youtube_id = self.youtube_uploader.upload_video(video_path, title, description)
        results['youtube_id'] = youtube_id
        
        # رفع إلى TikTok
        logger.info("=== بدء رفع الفيديو إلى TikTok ===")
        tiktok_success = self.tiktok_uploader.upload_video(video_path, title, description)
        results['tiktok_success'] = tiktok_success
        
        # حفظ النتائج
        with open('upload_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info("=== اكتمل رفع الفيديو ===")
        logger.info(f"YouTube ID: {youtube_id}")
        logger.info(f"TikTok Success: {tiktok_success}")
        
        return results

if __name__ == "__main__":
    # استخدام المثال
    uploader = VideoUploader()
    results = uploader.upload_to_all("final_video.mp4")
    print(json.dumps(results, ensure_ascii=False, indent=2))
