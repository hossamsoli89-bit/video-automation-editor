import os
import re
import requests
import random
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import Image, ImageDraw, ImageFont
import textwrap

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

def search_pexels_videos(query, per_page=3):
    """البحث عن فيديوهات باستخدام Pexels API"""
    if not PEXELS_API_KEY:
        print("خطأ: مفتاح Pexels API غير موجود.")
        return []
    
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={per_page}"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status() # يثير خطأ إذا كان الطلب غير ناجح
        data = response.json()
        return data.get('videos', [])
    except requests.exceptions.RequestException as e:
        print(f"خطأ في البحث في Pexels: {e}")
        return []


def download_video(video_data, filename):
    """تنزيل فيديو من Pexels"""
    try:
        # Pexels يوفر عدة جودة، سنختار الأفضل
        video_files = video_data.get('video_files', [])
        if not video_files:
            print(f"لا توجد ملفات فيديو للفيديو: {video_data.get('id')}")
            return None
        
        # اختيار الملف الأفضل بناءًا على الجودة (العرض × الارتفاع)
        best_quality_file = max(video_files, key=lambda f: f.get('width', 0) * f.get('height', 0), default=None)
        
        if best_quality_file:
            video_url = best_quality_file['link']
            print(f"تنزيل الفيديو من: {video_url}")
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filename
    except Exception as e:
        print(f"فشل في تنزيل الفيديو: {e}")
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
    # إنشاء صورة نصية
    img = Image.new('RGB', size, bgcolor)
    draw = ImageDraw.Draw(img)
    
    # محاولة استخدام خط عربي، والعودة إلى خط افتراضي إذا فشل
    try:
        # قم بتنزيل خط عربي ووضعه في نفس المجلد، أو استخدم مساراً مطلقاً
        # مثال: font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        # font = ImageFont.truetype(font_path, fontsize)
        font = ImageFont.load_default() # بديل بسيط
    except IOError:
        font = ImageFont.load_default()

    # استخدام textwrap لتقسيم النص إلى أسطر متعددة
    lines = textwrap.wrap(text, width=40) # ضبط العرض حسب الحاجة
    y_text = 10
    for line in lines:
        # الحصول على حجم النص لمحاذاته
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        # حساب المركز
        x_text = (size[0] - text_width) / 2
        # رسم النص
        draw.text((x_text, y_text), line, font=font, fill=color)
        y_text += text_height + 10

    # تحويل الصورة إلى كليب فيديو
    txt_clip = ImageClip(img)
    txt_clip = txt_clip.set_duration(duration)
    return txt_clip

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
        keywords = [word for word in sentence.split() if len(word) > 4]
        query = random.choice(keywords) if keywords else "happy people"
        
        print(f"البحث عن فيديوهات باستخدام الكلمة المفتاحية: {query}")
        videos = search_pexels_videos(query, per_page=1)
        
        if videos:
            video_data = videos[0]
            video_path = download_video(video_data, f"temp_video_{i}.mp4")
            
            if video_path:
                # تحميل الفيديو وتحديد مدته
                try:
                    clip = VideoFileClip(video_path)
                    # جعل مدة الفيديو مناسبة للجملة (مثلاً 3-5 ثوانٍ)
                    duration = min(5, clip.duration)
                    subclip = clip.subclip(0, duration)
                    video_clips.append(subclip)
                    
                    # إنشاء ترجمة للجملة
                    subtitles += create_subtitle(sentence, current_time, current_time + duration)
                    current_time += duration
                    clip.close() # إغلاق الكليب لتحرير الذاكرة
                except Exception as e:
                    print(f"فشل في معالجة ملف الفيديو {video_path}: {e}")
                    if os.path.exists(video_path):
                        os.remove(video_path) # حذف الملف التالف
            else:
                print(f"فشل تنزيل الفيديو للجملة: {sentence}")
        else:
            print(f"لم يتم العثور على فيديوهات للاستعلام: {query}")

    if not video_clips:
        print("لم يتم إنشاء أي مقاطع فيديو. إنهاء العملية.")
        return

    # 3. دمج كل مقاطع الفيديو
    print("دمج مقاطع الفيديو...")
    try:
        final_clip = concatenate_videoclips(video_clips, method="compose")
    except Exception as e:
        print(f"فشل في دمج مقاطع الفيديو: {e}")
        # تنظيف الملفات المؤقتة
        for i in range(len(sentences)):
            if os.path.exists(f"temp_video_{i}.mp4"):
                os.remove(f"temp_video_{i}.mp4")
        return

    # 4. إضافة الترجمات
    print("إضافة الترجمات...")
    try:
        # حفظ الترجمات في ملف
        with open("subtitles.srt", "w", encoding="utf-8") as f:
            f.write(subtitles)
        
        # إنشاء كليب الترجمات
        # (هذا جزء متقدم، سنقوم بتبسيطه الآن)
        # في الإصدارات الأحدث من MoviePy، قد تحتاج إلى استخدام SubtitlesClip بشكل مختلف
        # حالياً، سنقوم بإنشاء نصوص على الشاشة كبديل
        text_clips = []
        sentences_for_text = re.split(r'(?<=[.!?])\s+', SCRIPT.strip())
        current_time_for_text = 0
        for i, sentence in enumerate(sentences_for_text):
            duration = min(5, len(sentence.split()) * 0.5) # تقدير مدة العرض
            txt_clip = create_text_clip(sentence, duration)
            text_clips.append(txt_clip.set_start(current_time_for_text))
            current_time_for_text += duration

        # دمج النصوص مع الفيديو
        final_clip = CompositeVideoClip([final_clip] + text_clip)

    except Exception as e:
        print(f"فشل في إضافة النصوص: {e}")
        # لا نوقف العملية إذا فشلت إضافة النصوص

    # 5. حفظ الفيديو النهائي
    output_filename = "final_video.mp4"
    print(f"حفظ الفيديو النهائي باسم: {output_filename}")
    try:
        final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True, fps=24)
        print("اكتمل إنشاء الفيديو بنجاح!")
    except Exception as e:
        print(f"فشل في حفظ الفيديو النهائي: {e}")

    # 6. تنظيف الملفات المؤقتة
    print("تنظيف الملفات المؤقتة...")
    for i in range(len(sentences)):
        if os.path.exists(f"temp_video_{i}.mp4"):
            os.remove(f"temp_video_{i}.mp4")
    if os.path.exists("subtitles.srt"):
        os.remove("subtitles.srt")
    if os.path.exists("temp-audio.m4a"):
        os.remove("temp-audio.ma4")
    
    print("انتهت العملية.")

if __name__ == "__main__":
    main()
