import os
import shutil
import socket
import threading
import tkinter as tk
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse

UPLOAD_DIR = Path("저장된 파일")
UPLOAD_DIR.mkdir(exist_ok=True)


def get_local_ip() -> str:
    try:
        with socket.create_connection(("8.8.8.8", 53), timeout=1) as s:
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def unique_path(filename: str | None) -> Path:
    base = UPLOAD_DIR / (Path(filename or "").name or "uploaded_file")
    path, i = base, 1
    while path.exists():
        path = UPLOAD_DIR / f"{base.stem}({i}){base.suffix}"
        i += 1
    return path


SERVER_URL = f"http://{get_local_ip()}:8000"

app = FastAPI(
    title="📱 휴대폰 → 노트북 파일 전송",
    description=(
        f"- 휴대폰과 노트북이 **같은 와이파이**에 연결되어 있어야 합니다.\n"
        f"- 노트북에 **랜선**이 꽂혀 있다면 뽑아 주세요.\n"
        f"- 휴대폰 브라우저 접속 주소: **`{SERVER_URL}`**\n\n"
        f"### 사용 방법\n"
        f"1. 아래 **파일 선택** 버튼을 눌러 보낼 파일 고르기\n"
        f"2. 파란색 **Execute** 버튼 누르기 → 노트북 **`{UPLOAD_DIR.name}`** 폴더에 저장!"
    ),
    swagger_ui_parameters={
        "docExpansion": "full",
        "tryItOutEnabled": True,
        "defaultModelsExpandDepth": -1,
    },
)


@app.post("/upload", summary="파일 보내기")
def upload(file: UploadFile = File(..., description="보낼 파일 선택")):
    dest = unique_path(file.filename)
    try:
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"저장 실패: {e}")
    finally:
        file.file.close()
    return {"저장_완료": dest.name, "저장_폴더": UPLOAD_DIR.name}


@app.exception_handler(404)
def to_docs(_, __):
    return RedirectResponse("/docs")


def start_window():
    stop = lambda: os._exit(0)
    root = tk.Tk()
    root.title("파일 전송 서버")
    root.geometry("320x170")
    root.resizable(False, False)
    tk.Label(root, text="휴대폰 브라우저에 아래 주소를 입력하세요", pady=8).pack()
    tk.Label(root, text=SERVER_URL, font=("", 13, "bold"), fg="#2563eb").pack()
    tk.Label(root, text=f"저장 폴더: {UPLOAD_DIR.name}", fg="#6b7280", pady=6).pack()
    tk.Button(root, text="서버 끄기", command=stop, width=18, height=2).pack(pady=6)
    root.protocol("WM_DELETE_WINDOW", stop)
    root.mainloop()


if __name__ == "__main__":
    threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "0.0.0.0", "port": 8000, "log_level": "warning", "log_config": None},
        daemon=True,
    ).start()
    threading.Timer(1.2, webbrowser.open, args=[SERVER_URL]).start()
    start_window()
