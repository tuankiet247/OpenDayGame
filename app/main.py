from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import sys

# Ensure we can import from app module regardless of how this script is run
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.ai_manager import generate_question, analyze_results
except ImportError:
    from ai_manager import generate_question, analyze_results

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Game Configuration
GAME_CONFIG = {
    "logic": {
        "name": "Tư duy & Logic",
        "description": "Đánh giá tư duy logic, khả năng phân tích và sự kiên nhẫn.",
        "majors": ["CNTT", "AI"]
    },
    "creative": {
        "name": "Sáng tạo & Thẩm mỹ",
        "description": "Đánh giá sự sáng tạo, cảm nhận hình ảnh và tư duy thiết kế.",
        "majors": ["TKDH", "MKT"]
    },
    "business": {
        "name": "Giao tiếp & Kinh doanh",
        "description": "Đánh giá khả năng giao tiếp, thuyết phục và tư duy kinh doanh.",
        "majors": ["MKT", "NNA"]
    },
    "language": {
        "name": "Ngôn ngữ & Hội nhập",
        "description": "Đánh giá khả năng ngoại ngữ và tư duy toàn cầu.",
        "majors": ["NNA", "MKT"]
    }
}

class QuestionRequest(BaseModel):
    game_type: str 

class ResultRequest(BaseModel):
    scores: Dict[str, int]
    user_profile: Dict[str, str]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/generate-question")
async def api_generate_question(req: QuestionRequest):
    game_info = GAME_CONFIG.get(req.game_type)
    if not game_info:
        return {"error": "Invalid game type"}
    
    # Call AI
    question_data = generate_question(
        game_type=game_info["name"],
        description=game_info["description"],
        related_majors=game_info["majors"]
    )
    
    if question_data:
        return question_data
    
    return {"error": "AI could not generate a question"}

@app.post("/api/submit-result")
async def api_submit_result(req: ResultRequest):
    result = analyze_results(req.scores, req.user_profile)
    if result:
        return result
    else:
        return {
            "top_major": "CNTT", 
            "backup_majors": ["AI", "TKDH"],
            "reasoning": "Hệ thống AI đang bận, nhưng có vẻ bạn rất hợp với công nghệ!",
            "roadmap": "Học C -> Học Java -> Thực tập",
            "career_opportunities": "Dev, PM, BA",
            "badges": ["Future Tech Leader"]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
