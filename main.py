from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from solver import solve_puzzle, startindex  # ✅ 載入你的解題函式

app = FastAPI()

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定義接收格式
class SolveRequest(BaseModel):
    index_dict: dict
    boy_index: str

@app.post("/solve")
async def solve(request: SolveRequest):
    try:
        # 將位置字串轉成 tuple
        index_dict = {
            color: tuple(map(int, pos.split(",")))
            for color, pos in request.index_dict.items()
        }

        boy_index = startindex(request.boy_index)  # ex: "G" -> "G1"
        result = solve_puzzle(index_dict, boy_index, max_depth=10)

        return {
            "optimal_steps": result["optimal_steps"],
            "solution": result["solution"]
        }
    except Exception as e:
        return {"error": str(e)}

