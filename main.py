import os
import socket
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
import uvicorn

UPLOAD_DIR = Path("저장된 파일")
UPLOAD_DIR.mkdir(exist_ok=True)


def get_local_ip() -> str:
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip
    except Exception:
        return "127.0.0.1"
    


LOCAL_IP = get_local_ip()
SERVER_URL = f"http://{LOCAL_IP}:8000"

app = FastAPI(
    title="휴대폰 → 노트북 파일 전송",
    description=f"""
- 휴대폰과 노트북이 **같은 와이파이**에 연결되어 있어야 합니다.
- 노트북에 **랜선이 꽂혀 있다면 뽑아 주세요.**
- 휴대폰 브라우저에서 **이 주소(`{SERVER_URL}`)**에 접속하세요.

1. **POST /upload** 클릭
2. 오른쪽 **Try it out** 클릭
3. **파일 선택**으로 파일 고르기
4. **Execute** 클릭 → 노트북 **`uploads` 폴더**에 저장됨
""",
    version="1.0.0",
)


@app.post(
    "/upload",
    summary="파일 보내기",
    description="파일을 고르고 **Execute**를 누르면 `uploads` 폴더에 저장됩니다.",
)
async def upload(file: UploadFile = File(..., description="보낼 파일 선택")):
    safe_name = Path(file.filename).name if file.filename else "uploaded_file"
    dest_path = UPLOAD_DIR / safe_name

    if dest_path.exists():
        stem = dest_path.stem
        suffix = dest_path.suffix
        idx = 1
        while dest_path.exists():
            dest_path = UPLOAD_DIR / f"{stem}({idx}){suffix}"
            idx += 1

    try:
        with open(dest_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 실패: {e}")
    finally:
        await file.close()

    return {"저장_완료": dest_path.name}


@app.exception_handler(404)
def error(request: Request, exc):
    return RedirectResponse("/docs")


def open_browser_later():
    time.sleep(1.2)
    webbrowser.open(SERVER_URL)


def run_server():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="warning",
        log_config=None,
    )


def stop_server():
    os._exit(0)


def start_control_window():
    root = tk.Tk()
    root.title("파일 전송 서버")
    root.geometry("290x150")
    root.resizable(False, False)

    tk.Label(
        root,
        text=f"휴대폰 접속 주소:\n{SERVER_URL}",
        pady=12,
    ).pack()

    tk.Button(
        root,
        text="서버 끄기",
        command=stop_server,
        width=18,
        height=2,
    ).pack()

    root.protocol("WM_DELETE_WINDOW", stop_server)
    root.mainloop()


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=open_browser_later, daemon=True).start()
    start_control_window()