import tkinter as tk
from tkinter import filedialog, messagebox
import pyttsx3
import datetime
import os

# 음성 변환 함수
def text_to_speech():
    text = text_box.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("경고", "텍스트를 입력해주세요.")
        return

    # 음성 엔진 초기화
    engine = pyttsx3.init()

    # 파일 이름 형식 생성
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    short_text = text[:10].replace('\n', '').replace(' ', '')
    filename = f"{now}_{short_text}.mp3"

    # 파일 저장 경로 선택
    save_path = filedialog.asksaveasfilename(
        initialfile=filename,
        defaultextension=".mp3",
        filetypes=[("MP3 파일", "*.mp3")]
    )

    if not save_path:
        return

    try:
        engine.save_to_file(text, save_path)
        engine.runAndWait()
        messagebox.showinfo("완료", f"음성 파일이 저장되었습니다:\n{save_path}")
    except Exception as e:
        messagebox.showerror("오류", f"파일 저장 중 오류 발생: {e}")

# GUI 설정
root = tk.Tk()
root.title("텍스트 음성 변환기")
root.geometry("400x300")

# 라벨
tk.Label(root, text="텍스트 입력:").pack(pady=5)

# 텍스트 박스
text_box = tk.Text(root, height=10, width=40)
text_box.pack(pady=5)

# 변환 버튼
convert_button = tk.Button(root, text="음성으로 변환 및 저장", command=text_to_speech)
convert_button.pack(pady=10)

# 실행
root.mainloop()
