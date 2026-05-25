from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os
import logging
import time
from multiprocessing import Queue
from os import getenv
from prometheus_fastapi_instrumentator import Instrumentator
from logging_loki import LokiQueueHandler

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Prometheus 메트릭스 엔드포인트 (/metrics)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# 2. Loki 로그 핸들러 설정
loki_url = getenv("LOKI_ENDPOINT", "http://loki:3100/loki/api/v1/push")
loki_logs_handler = LokiQueueHandler(
    Queue(-1),
    url=loki_url,
    tags={"application": "fastapi"},
    version="1",
)
custom_logger = logging.getLogger("custom.access")
custom_logger.setLevel(logging.INFO)
custom_logger.addHandler(loki_logs_handler)

# --- 미들웨어 설정 (로그 수집의 핵심) ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    host = request.client.host if request.client else "127.0.0.1"
    log_message = (
        f'{host} - "{request.method} {request.url.path} HTTP/1.1" '
        f'{response.status_code} {duration:.3f}s'
    )
    custom_logger.info(log_message)
    return response

# To-Do 항목 모델
class TodoItem(BaseModel):
    id: int
    title: str
    description: str
    priority: str = "medium"
    category: str = "general"
    due_date: str = ""
    completed: bool
    status: str = "To Do"
    emoji: str = "📝"

# JSON 파일 경로
TODO_FILE = "todo.json"

# JSON 파일에서 To-Do 항목 로드 (하위 호환성 패치 포함)
def load_todos():
    if os.path.exists(TODO_FILE):
        try:
            with open(TODO_FILE, "r", encoding="utf-8") as file:
                todos = json.load(file)
            # 하위 호환성: 기존 데이터 필드 검사 및 동기화
            updated = False
            for todo in todos:
                if "status" not in todo:
                    todo["status"] = "Completed" if todo.get("completed", False) else "To Do"
                    updated = True
                if "emoji" not in todo:
                    todo["emoji"] = "📝"
                    updated = True
            if updated:
                save_todos(todos)
            return todos
        except Exception:
            return []
    return []

# JSON 파일에 To-Do 항목 저장
def save_todos(todos):
    with open(TODO_FILE, "w", encoding="utf-8") as file:
        json.dump(todos, file, indent=4, ensure_ascii=False)

# To-Do 목록 조회
@app.get("/todos", response_model=list[TodoItem])
def get_todos():
    return load_todos()

# 신규 To-Do 항목 추가
@app.post("/todos", response_model=TodoItem)
def create_todo(todo: TodoItem):
    todos = load_todos()
    # status와 completed 동기화
    if todo.status == "Completed":
        todo.completed = True
    elif todo.completed:
        todo.status = "Completed"
    else:
        todo.completed = False

    todos.append(todo.dict())
    save_todos(todos)
    return todo

# To-Do 항목 수정
@app.put("/todos/{todo_id}", response_model=TodoItem)
def update_todo(todo_id: int, updated_todo: TodoItem):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            # status와 completed 동기화
            if updated_todo.status == "Completed":
                updated_todo.completed = True
            elif updated_todo.completed:
                updated_todo.status = "Completed"
            else:
                updated_todo.completed = False
                if updated_todo.status == "Completed":
                    updated_todo.status = "To Do"

            todo.update(updated_todo.dict())
            save_todos(todos)
            return updated_todo
    raise HTTPException(status_code=404, detail="To-Do item not found")

# 완료된 To-Do 일괄 삭제
@app.delete("/todos/completed/clear", response_model=dict)
def clear_completed_todos():
    todos = load_todos()
    new_todos = [todo for todo in todos if not todo.get("completed", False)]
    save_todos(new_todos)
    return {"message": "Completed items cleared"}

# To-Do 항목 삭제
@app.delete("/todos/{todo_id}", response_model=dict)
def delete_todo(todo_id: int):
    todos = load_todos()
    new_todos = [todo for todo in todos if todo["id"] != todo_id]
    if len(new_todos) == len(todos):
        raise HTTPException(status_code=404, detail="To-Do item not found")
    save_todos(new_todos)
    return {"message": "To-Do item deleted"}

# HTML 파일 서빙
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r") as file:
        content = file.read()
    return HTMLResponse(content=content)