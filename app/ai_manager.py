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
Bạn là Game Master của trò chơi "Game chọn ngành – Earn Your Future" dành cho học sinh lớp 12 muốn vào Đại học FPT.
Mục tiêu: Giúp học sinh tìm ra ngành học phù hợp thông qua trắc nghiệm tính cách và tình huống.
Luật chơi: Không có đúng sai, mỗi lựa chọn cộng điểm cho các nhóm ngành khác nhau.
Các nhóm ngành chính:
1. CNTT (Công nghệ thông tin, Kỹ thuật phần mềm)
2. AI (Trí tuệ nhân tạo)
3. TKDH (Thiết kế đồ họa, Truyền thông đa phương tiện)
4. MKT (Digital Marketing, Quản trị kinh doanh)
5. NNA (Ngôn ngữ Anh, Ngôn ngữ Nhật - Nhóm Ngôn ngữ)
"""

def generate_question(game_type: str, description: str, related_majors: list):
    """
    Sinh câu hỏi cho một mini game cụ thể.
    """
    prompt = f"""
    {GAME_CONTEXT}
    
    Hãy tạo ra 01 câu hỏi trắc nghiệm thú vị, ĐỘC ĐÁO và KHÔNG TRÙNG LẶP cho Mini Game: "{game_type}".
    Mô tả game: {description}
    Các ngành liên quan chính: {', '.join(related_majors)}
    
    Hãy sáng tạo tình huống mới lạ, hài hước hoặc trending với Gen Z.
    
    Yêu cầu định dạng JSON (chỉ trả về JSON, không markdown):
    {{
        "question": "Nội dung câu hỏi hoặc tình huống",
        "options": [
            {{
                "id": "A",
                "text": "Nội dung lựa chọn A",
                "scores": {{ "CNTT": 0, "AI": 0, "TKDH": 0, "MKT": 0, "NNA": 0 }}  // Điểm số tương ứng (0-10)
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
    - Hãy phân phối điểm sao cho mỗi lựa chọn thể hiện rõ xu hướng tính cách của từng nhóm ngành.
    - Câu hỏi phải phù hợp học sinh lớp 12, ngôn ngữ trẻ trung, gen Z.
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
    
    Yêu cầu định dạng JSON (chỉ trả về JSON, không markdown):
    {{
        "top_major": "Tên ngành phù hợp nhất",
        "backup_majors": ["Ngành dự phòng 1", "Ngành dự phòng 2"],
        "reasoning": "Giải thích ngắn gọn tại sao chọn ngành này (khoảng 50 từ, giọng văn khích lệ, hài hước)",
        "roadmap": "Lộ trình học sơ lược (3 gạch đầu dòng ngắn)",
        "career_opportunities": "Cơ hội nghề nghiệp (3 vị trí hot)",
        "badges": ["Danh hiệu vui nhộn dựa trên điểm số (ví dụ: Logic Master, Design God)"]
    }}
    """
    
    return call_gemini(prompt)

def call_gemini(prompt: str):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": SITE_URL,
        "X-Title": APP_NAME,
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "google/gemini-2.0-flash-exp:free", # Using a potentially free or cheap model on OpenRouter, fallback to others if needed
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": { "type": "json_object" } # Force JSON if supported, otherwise prompt handles it
    }
    
    # Try multiple models if one specific isn't guaranteed, but start with flash-1.5 or 2.0-flash equivalent
    # Note: Model names on OpenRouter change. "google/gemini-flash-1.5" is common. 
    # Let's use "google/gemini-2.0-flash-001" if available or "google/gemini-pro-1.5"
    # To be safe for the user demo, I will use "google/gemini-pro-1.5" as it is standard.
    # User asked for Gemini.
    data["model"] = "google/gemini-2.5-flash-lite" 

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        # Clean up markdown code blocks if present
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
             content = content.replace("```", "")
             
        return json.loads(content.strip())
    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        # Return fallback data if AI fails
        return None
