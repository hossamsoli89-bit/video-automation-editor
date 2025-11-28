import os
import re
import requests
import random
import sys
import traceback
import tempfile
import shutil

# --- محاولة استيراد المكتبات مع معالجة الأخطاء ---
try:
    from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
    from moviepy.video.tools.subtitles import SubtitlesClip
    from PIL import Image, ImageDraw, ImageFont
    import textwrap
except ImportError as e:
    print(f"خطأ في استيراد المكتبات: {e}")
    print("تأكد من تثبيت جميع المكتبات المطلوبة.")
    sys.exit(1)

# --- الإعدادات ---
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

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
    if not PEXELS_API_KEY:
        print("خطأ: مفتاح Pexels API غير موجود.")
        return []
    
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={per_page}"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('videos', [])
    except requests.exceptions.RequestException as e:
        print(f"خطأ في البحث في Pexels: {e}")
        return []


def download_video(video_data, filename):
    """تنزيل فيديو من Pexels"""
    try:
        video_files = video_data.get('video_files', [])
        if not video_files:
            print(f"لا توجد ملفات فيديو للفيديو: {video_data.get('id')}")
            return None
        
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
        print("تحذير: استخدام الخط الافتراضي لأنه لم يتم العثور على خط مناسب.")

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

# --- المنطق الرئيسي ---

def main():
    print("بدء عملية إنشاء الفيديو...")
    
    # إنشاء دليل مؤقت
    temp_dir = tempfile.mkdtemp()
    print(f"تم إنشاء دليل مؤقت: {temp_dir}")
    
    try:
        # تقسيم السيناريو إلى جمل
        sentences = re.split(r'(?<=[.!?])\s+', SCRIPT.strip())
        print(f"تم تقسيم السيناريو إلى {len(sentences)} جملة للبحث.")

        video_clips = []
        current_time = 0
        subtitles = ""
        
        # معالجة كل جملة
        for i, sentence in enumerate(sentences):
            print(f"معالجة الجملة {i+1}: '{sentence[:30]}...'")
            
            # اختيار كلمة مفتاحية للبحث
            keywords = [word for word in sentence.split() if len(word) > 4]
            query = random.choice(keywords) if keywords else "happy people"
            
            print(f"البحث عن فيديوهات باستخدام الكلمة المفتاحية: {query}")
            videos = search_pexels_videos(query, per_page=1)
            
            if videos:
                video_data = videos[0]
                video_path = os.path.join(temp_dir, f"temp_video_{i}.mp4")
                
                if download_video(video_data, video_path):
                    try:
                        clip = VideoFileClip(video_path)
                        duration = min(5, clip.duration)
                        subclip = clip.subclip(0, duration)
                        video_clips.append(subclip)
                        
                        subtitles += create_subtitle(sentence, current_time, current_time + duration)
                        current_time += duration
                        clip.close()
                    except Exception as e:
                        print(f"فشل في معالجة ملف الفيديو {video_path}: {e}")
                        traceback.print_exc()
                else:
                    print(f"فشل تنزيل الفيديو للجملة: {sentence}")
            else:
                print(f"لم يتم العثور على فيديوهات للاستعلام: {query}")

        if not video_clips:
            print("لم يتم إنشاء أي مقاطع فيديو. إنهاء العملية.")
            # إنشاء فيديو بديل إذا لم يتم العثور على فيديوهات
            print("إنشاء فيديو بديل...")
            img = Image.new('RGB', (1280, 720), color='black')
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((50, 50), "لم يتم العثور على فيديوهات", fill='white', font=font)
            img.save(os.path.join(temp_dir, "fallback.jpg"))
            clip = ImageClip(os.path.join(temp_dir, "fallback.jpg"))
            clip = clip.set_duration(5)
            video_clips.append(clip)

        # دمج مقاطع الفيديو
        print("دمج مقاطع الفيديو...")
        try:
            final_clip = concatenate_videoclips(video_clips, method="compose")
        except Exception as e:
            print(f"فشل في دمج مقاطع الفيديو: {e}")
            traceback.print_exc()
            return

        # إضافة النصوص
        print("إضافة النصوص...")
        try:
            text_clips = []
            sentences_for_text = re.split(r'(?<=[.!?])\s+', SCRIPT.strip())
            current_time_for_text = 0
            for i, sentence in enumerate(sentences_for_text):
                duration = min(5, len(sentence.split()) * 0.5)
                txt_clip = create_text_clip(sentence, duration)
                text_clips.append(txt_clip.set_start(current_time_for_text))
                current_time_for_text += duration

            final_clip = CompositeVideoClip([final_clip] + text_clips)
        except Exception as e:
            print(f"فشل في إضافة النصوص: {e}")
            traceback.print_exc()

        # حفظ الفيديو النهائي
        output_filename = os.path.join(temp_dir, "final_video.mp4")
        print(f"حفظ الفيديو النهائي باسم: {output_filename}")
        try:
            final_clip.write_videofile(
                output_filename, 
                codec='libx264', 
                audio_codec='aac', 
                temp_audiofile=os.path.join(temp_dir, 'temp-audio.m4a'), 
                remove_temp=True, 
                fps=24,
                verbose=False,
                logger=None
            )
            print("اكتمل إنشاء الفيديو بنجاح!")
            
            # نسخ الفيديو النهائي إلى مسار يمكن الوصول إليه
            final_output_path = os.path.join(os.getcwd(), "final_video.mp4")
            shutil.copy2(output_filename, final_output_path)
            print(f"تم نسخ الفيديو النهائي إلى: {final_output_path}")
            
            # التحقق من وجود الملف
            if os.path.exists(final_output_path):
                print(f"تم التحقق من وجود الفيديو النهائي: {final_output_path}")
                print(f"حجم الملف: {os.path.getsize(final_output_path)} bytes")
            else:
                print("تحذير: الفيديو النهائي غير موجود بعد النسخ!")
                
        except Exception as e:
            print(f"فشل في حفظ الفيديو النهائي: {e}")
            traceback.print_exc()
            return
    
    finally:
        # تنظيف الملفات المؤقتة
        print("تنظيف الملفات المؤقتة...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("انتهت العملية.")

if __name__ == "__main__":
    main()
