# في video_editor.py
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_youtube_simple(video_path, title="فيديو تلقائي"):
    """رفع الفيديو باستخدام Service Account (الطريقة الأسهل)"""
    try:
        # تحميل مفتاح Service Account
        service_account_info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY"))
        
        # إنشاء بيانات الاعتماد
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        # إنشاء خدمة YouTube
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # إعداد الطلب
        request_body = {
            'snippet': {
                'title': title,
                'description': 'فيديو تم إنشاؤه تلقائيًا',
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public'
            }
        }
        
        # رفع الفيديو
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )
        
        response = request.execute()
        print(f"✅ تم رفع الفيديو! ID: {response['id']}")
        return response['id']
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None
