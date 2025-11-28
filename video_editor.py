import os
import requests
import re
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import Image
import random

# --- الإعدادات ---
# سيتم جلب هذه القيم من أسرار GitHub (secrets)
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

# --- سيناريو الفيديو (مؤقت) ---
# في التطبيق الحقيقي، سنقوم بجلب هذا من Google Apps Script
SCRIPT = """
أهلًا بالجميع! كيف حالكم اليوم؟ هل تشعرون بأنكم بحاجة لجرعة إضافية من السعادة؟
أنا متأكد أن الإجابة هي نعم! كلنا نبحث عن السعادة، لكن أحيانًا ننسى أنها تكمن في أبسط الأشياء.
لذلك، قررت أن أبدأ تحديًا جديدًا ومثيرًا: "30 يوم سعادة"!
فكرة بسيطة جدًا: لمدة 30 يومًا، سأشارككم تحديًا يوميًا.
تحدي اليوم الأول بسيط جدًا: ابتسم لشخص غريب! نعم، ابتسم فقط!
"""

# --- وظائف مساعدة ---

def search_pexels_videos(query, per_page=5):
    """البحث عن فيديوهات باستخدام Pexels API"""
    if not PEXELS_API_KEY:
        print("خطأ: مفتاح Pexels API غير موجود.")
        return []
    
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={per_page}"
    headers = {"Authorization": PEXELS_API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('videos', [])
    else:
        print(f"خطأ في البحث في Pexels: {response.status_code}")
        return []

def download_video(video_data, filename):
    """تنزيل فيديو من Pexels"""
    # Pexels يوفر عدة جودة، سنختار الأفضل
    video_files = video_data.get('video_files', [])
    best_quality_file = max(video_files, key=lambda f: f.get('width', 0) * f.get('height', 0), default=None)
    
    if best_quality_file:
        video_url = best_quality_file['link']
        response = requests.get(video_url, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filename
    return None

def create_subtitle(text, start_time, end_time):
    """إنشاء ملف ترجمة فرعي بسيط لكل جملة"""
    # تحويل الوقت إلى صيغة srt
    def format_time(t):
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        milliseconds = int((t - int(t)) * 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    
    return f"{format_time(start_time)} --> {format_time(end_time)}\n{text}\n\n"

# --- المنطق الرئيسي ---

def main():
    print("بدء عملية إنشاء الفيديو...")
    
    # 1. تقسيم السيناريو إلى جمل للبحث
    sentences = re.split(r'(?<=[.!?])\s+', SCRIPT.strip())
    print(f"تم تقسيم السيناريو إلى {len(sentences)} جملة للبحث.")

    video_clips = []
    current_time = 0
    subtitles = ""
    
    # 2. البحث عن فيديو وتنزيله لكل جملة
    for i, sentence in enumerate(sentences):
        print(f"معالجة الجملة {i+1}: '{sentence[:30]}...'")
        
        # استخراج الكلمات المفتاحية للبحث (ببساطة)
        keywords = [word for word in sentence.split() if len(word) > 3]
        query = random.choice(keywords) if keywords else "happy people"
        
        videos = search_pexels_videos(query, per_page=1)
        if videos:
            video_data = videos[0]
            video_path = download_video(video_data, f"temp_video_{i}.mp4")
            
            if video_path:
                # تحميل الفيديو وتحديد مدته
                clip = VideoFileClip(video_path)
                # جعل مدة الفيديو مناسبة للجملة (مثلاً 3-5 ثواني)
                duration = min(5, clip.duration)
                subclip = clip.subclip(0, duration)
                video_clips.append(subclip)
                
                # إنشاء ترجمة للجملة
                subtitles += create_subtitle(sentence, current_time, current_time + duration)
                current_time += duration
            else:
                print(f"فشل تنزيل الفيديو للجملة: {sentence}")
        else:
            print(f"لم يتم العثور على فيديوهات للاستعلام: {query}")

    if not video_clips:
        print("لم يتم إنشاء أي مقاطع فيديو. إنهاء العملية.")
        return

    # 3. دمج كل مقاطع الفيديو
    print("دمج مقاطع الفيديو...")
    final_clip = concatenate_videoclips(video_clips, method="compose")
    
    # 4. إضافة الترجمات
    # (هذا جزء متقدم، سنقوم بتبسيطه الآن)
    # سنقوم بحفظ الترجمات في ملف أولاً
    with open("subtitles.srt", "w", encoding="utf-8") as f:
        f.write(subtitles)
    
    # 5. حفظ الفيديو النهائي
    output_filename = "final_video.mp4"
    print(f"حفظ الفيديو النهائي باسم: {output_filename}")
    final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)
    
    print("اكتمل إنشاء الفيديو بنجاح!")

if __name__ == "__main__":
    main()
