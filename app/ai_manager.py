import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SITE_URL = os.getenv("site_url")
APP_NAME = os.getenv("appName")

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Prompt templates
GAME_CONTEXT = """
Bạn là tư vấn viên hướng nghiệp chuyên sâu cho học sinh lớp 12 chuẩn bị thi đại học.
Nhiệm vụ: Đặt câu hỏi trắc nghiệm để khám phá tính cách, tư duy và sở thích của học sinh, từ đó gợi ý ngành học phù hợp nhất.
Các ngành học cần tư vấn:
1. CNTT (Công nghệ thông tin, Kỹ thuật phần mềm): Tư duy logic, thích code, giải quyết vấn đề kỹ thuật.
2. AI (Trí tuệ nhân tạo): Thích toán, dữ liệu, công nghệ mới, thích nghiên cứu.
3. TKDH (Thiết kế đồ họa): Có gu thẩm mỹ, sáng tạo, thích hình ảnh, nghệ thuật.
4. MKT (Marketing, Kinh doanh): Hoạt ngôn, thích giao tiếp, kinh tế, quản lý, sáng tạo nội dung.
5. NNA (Ngôn ngữ): Yêu thích ngoại ngữ, văn hóa, giao tiếp quốc tế.
"""

import random


# Offline Data Fallback
# OFFLINE_QUESTIONS Removed - Using AI Only

def analyze_results(scores: dict, user_profile: dict):
    """
    Phân tích kết quả và đưa ra gợi ý.
    """
    prompt = f"""
    {GAME_CONTEXT}
    
    Thông tin người chơi:
    - Tên: {user_profile.get('name', 'Bạn học sinh')}
    - Điểm số các nhóm ngành sau khi chơi: {json.dumps(scores)}
    
    Hãy đóng vai chuyên gia tư vấn hướng nghiệp của ĐH FPT và đưa ra báo cáo kết quả.
    
    Yêu cầu định dạng JSON (chỉ trả về JSON, không markdown, không giải thích gì thêm):
    {{
        "top_major": "Tên ngành phù hợp nhất",
        "backup_majors": ["Ngành dự phòng 1", "Ngành dự phòng 2"],
        "reasoning": "Giải thích ngắn gọn tại sao chọn ngành này (khoảng 50 từ, giọng văn khích lệ, hài hước)",
        "roadmap": "Lộ trình học sơ lược (3 gạch đầu dòng ngắn)",
        "career_opportunities": "Cơ hội nghề nghiệp (3 vị trí hot)",
        "badges": ["Danh hiệu vui nhộn dựa trên điểm số (ví dụ: Logic Master, Design God)"]
    }}
    - KHÔNG được thêm ```json ở đầu hay cuối. Chỉ trả về text thuần là JSON.
    """
    
    result = call_gemini(prompt)
    if result:
        return result
        
    # Fallback Offline Result
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_major = sorted_scores[0][0]
    
    reasons = {
        "CNTT": "Bạn có tư duy logic sắc bén, thích giải quyết vấn đề. Code chính là chân ái!",
        "AI": "Bạn thích sự mới mẻ, công nghệ tương lai và những bài toán khó. AI đang chờ bạn!",
        "TKDH": "Tâm hồn bay bổng, yêu cái đẹp và màu sắc. Sáng tạo là vũ khí của bạn!",
        "MKT": "Khéo léo, hoạt ngôn và nắm bắt tâm lý tốt. Bạn sinh ra để làm Marketing!",
        "NNA": "Yêu thích văn hóa, ngôn ngữ và kết nối toàn cầu. Công dân toàn cầu chính là bạn!"
    }
    
    return {
        "top_major": f"Ngành {top_major}",
        "backup_majors": [f"Ngành {sorted_scores[1][0]}", f"Ngành {sorted_scores[2][0]}"],
        "reasoning": reasons.get(top_major, "Bạn rất tài năng và phù hợp với môi trường năng động của FPT!"),
        "roadmap": "Năm 1: Tiếng Anh & Nền tảng -> Năm 2: Chuyên ngành -> Năm 3: OJT (Thực tập) -> Năm 4: Đồ án",
        "career_opportunities": "Chuyên viên tại FPT Software, Startup Founder, Freelancer quốc tế",
        "badges": ["FPT Future Star", "Gen Z Tài Năng"]
    }

def evaluate_question_options(question_data: dict, game_type: str, description: str, related_majors: list):
    """
    Đánh giá điểm số cho các lựa chọn của câu hỏi có sẵn bằng AI.
    """
    options_text = ""
    for opt in question_data["options"]:
        options_text += f'{opt["label"]}. {opt["text"]}\n'

    prompt = f"""
    {GAME_CONTEXT}
    
    Hãy đóng vai chuyên gia hướng nghiệp, phân tích câu hỏi và các lựa chọn sau đây để gán điểm số phù hợp cho từng ngành học.
    
    Chủ đề: "{game_type}" ({description})
    Câu hỏi (ID {question_data.get('id')}): "{question_data["question_text"]}"
    
    Các lựa chọn:
    {options_text}
    
    Các ngành cần chấm điểm: CNTT, AI, TKDH, MKT, NNA.
    Điểm số từ 0 đến 5 cho mỗi ngành, dựa trên mức độ phù hợp của lựa chọn đó với tố chất của ngành.
    
    Yêu cầu định dạng JSON (chỉ trả về JSON, không markdown):
    {{
        "question": "{question_data["question_text"]}",
        "options": [
            {{
                "id": "A",
                "text": "Nội dung lựa chọn A",
                "scores": {{ "CNTT": x, "AI": x, "TKDH": x, "MKT": x, "NNA": x }}
            }},
            {{
                "id": "B",
                "text": "Nội dung lựa chọn B",
                "scores": {{ "CNTT": x, "AI": x, "TKDH": x, "MKT": x, "NNA": x }}
            }},
            {{
                "id": "C",
                "text": "Nội dung lựa chọn C",
                "scores": {{ "CNTT": x, "AI": x, "TKDH": x, "MKT": x, "NNA": x }}
            }}
        ]
    }}
    
    Lưu ý: 
    - Giữ nguyên nội dung text của câu hỏi và các lựa chọn.
    - KHÔNG được thêm ```json ở đầu hay cuối. Chỉ trả về text thuần là JSON.
    """
    
    # Add randomness to prompt to prevent AI Caching
    prompt += f"\n[Request ID: {random.randint(10000, 99999)}]"
    
    print(f"Calling AI for Question ID: {question_data.get('id')}")
    result = call_gemini(prompt)
    if result and "options" in result:
        # Merge AI scores with original question data to ensure text correctness
        ai_options_map = {opt.get("id"): opt.get("scores") for opt in result["options"]}
        
        final_options = []
        for opt in question_data["options"]:
            # Default empty scores
            scores = { "CNTT": 0, "AI": 0, "TKDH": 0, "MKT": 0, "NNA": 0 }
            
            # Try to get scores from AI result matching label (A, B, C)
            if opt["label"] in ai_options_map:
                scores = ai_options_map[opt["label"]]
            
            final_options.append({
                "id": opt["label"],
                "text": opt["text"],
                "scores": scores
            })
            
        return {
            "id": question_data.get("id"),
            "question": question_data["question_text"],
            "options": final_options
        }

    # Fallback if AI fails
    fallback_options = []
    for opt in question_data["options"]:
        scalar = opt.get("score", 1)
        scores = { "CNTT": 0, "AI": 0, "TKDH": 0, "MKT": 0, "NNA": 0 }
        for major in related_majors:
            scores[major] = scalar
        fallback_options.append({
            "id": opt["label"],
            "text": opt["text"],
            "scores": scores
        })
        
    return {
        "id": question_data.get("id"),
        "question": question_data["question_text"],
        "options": fallback_options
    }

def call_gemini(prompt: str):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": SITE_URL,
        "X-Title": APP_NAME,
        "Content-Type": "application/json"
    }
    
    model = "xiaomi/mimo-v2-flash:free"
    
    if not OPENROUTER_API_KEY:
        print("WARNING: OPENROUTER_API_KEY is not set!")

    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            # Clean up code blocks
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        else:
            print(f"Model {model} failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Error with model {model}: {e}")

    print("AI request failed.")
    return None
