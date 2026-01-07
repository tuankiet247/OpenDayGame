from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import sys
import json

# Ensure we can import from app module regardless of how this script is run
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.ai_manager import analyze_results, evaluate_question_options
except ImportError:
    from ai_manager import analyze_results, evaluate_question_options

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load Questions
QUESTIONS_DB = []
try:
    with open(os.path.join(BASE_DIR, "question.json"), "r", encoding="utf-8") as f:
        QUESTIONS_DB = json.load(f)
except Exception as e:
    print(f"Error loading question.json: {e}")

# Index questions by category for faster access
QUESTIONS_BY_CATEGORY = {}
for q in QUESTIONS_DB:
    cat = q.get("category_id")
    if cat:
        if cat not in QUESTIONS_BY_CATEGORY:
            QUESTIONS_BY_CATEGORY[cat] = []
        QUESTIONS_BY_CATEGORY[cat].append(q)

# Sort questions in each category by ID to ensure deterministic order
for cat in QUESTIONS_BY_CATEGORY:
    QUESTIONS_BY_CATEGORY[cat].sort(key=lambda x: int(x.get("id", 0)))
    print(f"Category {cat}: loaded {len(QUESTIONS_BY_CATEGORY[cat])} questions (IDs: {[q.get('id') for q in QUESTIONS_BY_CATEGORY[cat]]})")

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
    question_index: int = 0

class ResultRequest(BaseModel):
    scores: Dict[str, int]
    user_profile: Dict[str, str]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/generate-question")
async def api_generate_question(req: QuestionRequest):
    # Use req.game_type to match "category_id" in quesiton.json
    # "logic", "creative", "business", "language"
    
    questions = QUESTIONS_BY_CATEGORY.get(req.game_type, [])
    
    if not questions:
        print(f"Error: Category {req.game_type} not found or empty.")
        return {"error": f"No questions found for category: {req.game_type}"}

    print(f"DEBUG: Type={req.game_type} Index={req.question_index} Total={len(questions)}")

    # Strict index checking to avoid repetition loops
    if 0 <= req.question_index < len(questions):
        selected_question = questions[req.question_index]
        print(f"DEBUG: Selected Question ID: {selected_question.get('id')}")
        
        # Get game description for AI context
        game_desc = ""
        game_majors = []
        if req.game_type in GAME_CONFIG:
             game_desc = GAME_CONFIG[req.game_type]["description"]
             game_majors = GAME_CONFIG[req.game_type]["majors"]
        
        # Use AI to evaluate options and assign scores
        return evaluate_question_options(
            question_data=selected_question,
            game_type=req.game_type,
            description=game_desc,
            related_majors=game_majors
        )
    
    print(f"Error: Index {req.question_index} out of bounds for category {req.game_type}")
    return {"error": "Question index out of bounds"}

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
