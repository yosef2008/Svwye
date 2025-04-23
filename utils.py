import torch
import numpy as np
import tempfile
import imageio
from typing import List, Dict
from diffusers import TextToVideoZeroPipeline

# 1. تحميل الأنبوب مرة واحدة (بدون إعادة تحميل عند كل استدعاء)
PIPE = TextToVideoZeroPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda" if torch.cuda.is_available() else "cpu")  # 6

# 2. مولّد لتثبيت البذرة (Seed) لثبات النتائج
GEN = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu")

def chunk_text(text: str, max_words: int = 100) -> List[str]:
    """
    يقسم النص إلى أجزاء كل منها بحد أقصى `max_words` كلمات.
    مثال: 3000 كلمة → 30 برومبتاً من 100 كلمة 7.
    """
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def generate_video(prompts: List[str], settings: Dict) -> str:
    """
    يولد فيديوً من قائمة برومبتات النص `prompts` اعتمادًا على الإعدادات:
      - settings['type']: "كرتوني" أو "واقعي"
      - settings['aspect']: نسبة العرض:الارتفاع (مثلاً "9:16")
      - settings['quality']: "منخفض"، "متوسط"، "عالي"، "فائق الدقة"
      - settings['fps']: إطارات في الثانية (مثلاً "24fps")
    """
    # 3. اختيار الوصف الأسلوبي
    style = "cartoon style" if settings['type'] == "كرتوني" else "photorealistic"  # 8

    # 4. خريطة n نسبة العرض:الارتفاع إلى الأبعاد بالبكسل
    aspect_map = {
        "9:16": (512, 896), "16:9": (896, 512),
        "1:1": (768, 768), "4:5": (768, 960)
    }
    width, height = aspect_map.get(settings['aspect'], (512, 512))  # 9

    # 5. إطارات في الثانية
    fps = int(settings['fps'].replace("fps", ""))

    # 6. مقياس الإرشاد (guidance_scale) حسب الجودة
    quality_map = {
        "منخفض": 5.0, "متوسط": 7.5,
        "عالي": 10.0, "فائق الدقة": 15.0
    }
    guidance = quality_map.get(settings['quality'], 7.5)  # 10

    # 7. إعداد البرومبتات النهائية بإضافة الوصف الأسلوبي
    styled_prompts = [f"{p}, {style}" for p in prompts]

    # 8. تحديد طول الفيديو وعدد الأجزاء (chunks) حسب حجم البرومبتات
    chunk_size = 8  # عدد الإطارات الافتراضي لكل استدعاء 11
    total_frames = len(styled_prompts) * chunk_size
    chunk_ids = np.arange(0, total_frames, chunk_size - 1)

    all_frames = []
    for i, prompt in enumerate(styled_prompts):
        # 9. إعداد قائمة الإطارات للحفاظ على الاتساق الزمني
        ch_start = chunk_ids[i]
        ch_end = total_frames if i == len(chunk_ids)-1 else chunk_ids[i+1]
        frame_ids = [0] + list(range(ch_start, ch_end))

        GEN.manual_seed(42)  # تثبيت البذرة لنتائج قابلة للتكرار

        output = PIPE(
            prompt=prompt,
            video_length=len(frame_ids),
            generator=GEN,
            frame_ids=frame_ids,
            height=height,
            width=width,
            guidance_scale=guidance
        )
        all_frames.extend(output.images[1:])  # نتجاهل الإطار الأول المكرر

    # 10. حفظ الإطارات في ملف MP4 مؤقت
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    imageio.mimsave(temp.name, [(f * 255).astype("uint8") for f in all_frames], fps=fps)
    return temp.name
