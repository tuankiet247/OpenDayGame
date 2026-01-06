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


def generate_question(game_type: str, description: str, related_majors: list):
    """
    Sinh câu hỏi cho một mini game cụ thể. Nếu AI lỗi, dùng câu hỏi Offline.
    """
    prompt = f"""
    {GAME_CONTEXT}
    
    Hãy đóng vai chuyên gia hướng nghiệp, tạo ra 01 câu hỏi trắc nghiệm dạng TÌNH HUỐNG (Situational Judgment Test) cho chủ đề: "{game_type}".
    Mô tả chủ đề: {description}
    Các ngành trọng tâm cần đánh giá: {', '.join(related_majors)} (nhưng hãy mở rộng các phương án để đánh giá cả các ngành khác nếu phù hợp).
    
    Yêu cầu quan trọng:
    1. KHÔNG hỏi trực tiếp kiểu "Bạn thích làm việc gì?" hay liệt kê tên ngành ra đáp án.
    2. Tình huống phải THỰC TẾ với học sinh lớp 12 (ví dụ: làm bài tập nhóm, tham gia CLB, sử dụng mạng xã hội, giải trí cuối tuần...).
    3. TRÁNH dùng thuật ngữ chuyên ngành khó hiểu. Hãy dùng ngôn ngữ đời thường, gần gũi.
    4. Các lựa chọn (A, B, C) là phản xạ tự nhiên:
       - Một lựa chọn thể hiện tố chất của nhóm "{game_type}".
       - Các lựa chọn còn lại thể hiện tố chất của nhóm ngành khác.
    
    Ví dụ tốt: "Khi lướt TikTok thấy một video trend biến hình cực ngầu, suy nghĩ đầu tiên của bạn là?"
    -> A. "Họ edit bằng app gì mà mượt thế nhỉ?" (Tò mò công cụ -> CNTT/AI)
    -> B. "Màu đẹp quá, góc quay này nghệ thật!" (Cảm nhận thẩm mỹ -> TKDH)
    -> C. "Video này chắc chắn shop tài trợ, view cao thế này bán đắt hàng lắm." (Tư duy thị trường -> MKT)
    
    Yêu cầu định dạng JSON (chỉ trả về JSON, không markdown, không giải thích gì thêm):
    {{
        "question": "Nội dung tình huống...",
        "options": [
            {{
                "id": "A",
                "text": "Nội dung lựa chọn A",
                "scores": {{ "CNTT": 0, "AI": 0, "TKDH": 0, "MKT": 0, "NNA": 0 }}
            }},
            {{
                "id": "B",
                "text": "Nội dung lựa chọn B",
                "scores": {{ "CNTT": 0, "AI": 0, "TKDH": 0, "MKT": 0, "NNA": 0 }}
            }},
            {{
                "id": "C",
                "text": "Nội dung lựa chọn C",
                "scores": {{ "CNTT": 0, "AI": 0, "TKDH": 0, "MKT": 0, "NNA": 0 }}
            }}
        ]
    }}
    
    Lưu ý:
    - Hãy phân phối điểm số (scores) thật chuẩn xác. Ví dụ nếu chọn phương án thiên về sáng tạo thì điểm TKDH/MKT phải cao, CNTT/AI thấp.
    - Ngôn ngữ: Chân thành, khách quan, phù hợp với tâm lý học sinh lớp 12 đang băn khoăn chọn nghề.
    - KHÔNG được thêm ```json ở đầu hay cuối. Chỉ trả về text thuần là JSON.
    """
    
    return call_gemini(prompt)

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
