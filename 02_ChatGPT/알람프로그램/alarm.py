#pip install tkcalendar mysql-connector-python pygame plyer

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import Calendar
import threading
import time
import datetime
import mysql.connector
from pygame import mixer
from plyer import notification
import os

# MySQL 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'user': 'aloha',
    'password': '123456',
    'database': 'aloha'
    
}

# DB 초기화 함수
def init_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS alarm (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100),
                        sound_path VARCHAR(255),
                        alarm_time DATETIME
                    )''')
    conn.commit()
    conn.close()

# 알람 관리 클래스
class AlarmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("알람 관리 프로그램")
        self.root.geometry("800x600")

        self.dashboard_frame = ttk.Frame(root)
        self.dashboard_frame.pack(fill="both", expand=True)

        self.create_dashboard()
        init_db()
        self.refresh_alarms()

        # 알람 모니터링 스레드 시작
        threading.Thread(target=self.check_alarms, daemon=True).start()

    def create_dashboard(self):
        ttk.Label(self.dashboard_frame, text="📅 등록된 알람 목록", font=("Arial", 18, "bold")).pack(pady=10)

        self.tree = ttk.Treeview(self.dashboard_frame, columns=("이름", "시간", "소리"), show='headings', height=15)
        self.tree.heading("이름", text="이름")
        self.tree.heading("시간", text="알람 시간")
        self.tree.heading("소리", text="알람 소리")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree.bind('<Double-1>', self.open_alarm_editor)

        btn_frame = ttk.Frame(self.dashboard_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="알람 등록", command=self.open_add_alarm).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="선택 알람 삭제", command=self.delete_alarm).pack(side="left", padx=5)

    def refresh_alarms(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, alarm_time, sound_path FROM alarm")
        for row in cursor.fetchall():
            self.tree.insert('', 'end', iid=row[0], values=(row[1], row[2], row[3]))
        conn.close()

    def open_add_alarm(self):
        win = tk.Toplevel(self.root)
        win.title("알람 등록")
        win.geometry("400x400")

        ttk.Label(win, text="알람 이름:").pack(pady=5)
        name_entry = ttk.Entry(win)
        name_entry.pack(pady=5)

        ttk.Label(win, text="알람 날짜 선택:").pack(pady=5)
        cal = Calendar(win, date_pattern='yyyy-mm-dd')
        cal.pack(pady=5)

        ttk.Label(win, text="알람 시간 입력 (HH:MM 형식):").pack(pady=5)
        time_entry = ttk.Entry(win)
        time_entry.insert(0, "07:00")
        time_entry.pack(pady=5)

        ttk.Label(win, text="알람 소리 선택:").pack(pady=5)
        sound_path = tk.StringVar(value="c:/alarm/기본.mp3")
        ttk.Combobox(win, textvariable=sound_path, values=self.get_sound_files(), width=40).pack(pady=5)

        def save_alarm():
            name = name_entry.get()
            date_str = cal.get_date()
            time_str = time_entry.get()
            alarm_datetime = f"{date_str} {time_str}:00"

            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO alarm (name, sound_path, alarm_time) VALUES (%s, %s, %s)",
                           (name, sound_path.get(), alarm_datetime))
            conn.commit()
            conn.close()
            messagebox.showinfo("성공", "알람이 등록되었습니다!")
            win.destroy()
            self.refresh_alarms()

        ttk.Button(win, text="등록", command=save_alarm).pack(pady=20)

    def open_alarm_editor(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, alarm_time, sound_path FROM alarm WHERE id=%s", (selected,))
        data = cursor.fetchone()
        conn.close()

        win = tk.Toplevel(self.root)
        win.title("알람 수정")
        win.geometry("400x400")

        ttk.Label(win, text="알람 이름:").pack(pady=5)
        name_entry = ttk.Entry(win)
        name_entry.insert(0, data[1])
        name_entry.pack(pady=5)

        ttk.Label(win, text="알람 날짜 선택:").pack(pady=5)
        cal = Calendar(win, date_pattern='yyyy-mm-dd')
        cal.pack(pady=5)

        ttk.Label(win, text="알람 시간 입력 (HH:MM 형식):").pack(pady=5)
        time_entry = ttk.Entry(win)
        time_entry.insert(0, data[2].strftime('%H:%M'))
        time_entry.pack(pady=5)

        ttk.Label(win, text="알람 소리 선택:").pack(pady=5)
        sound_path = tk.StringVar(value=data[3])
        ttk.Combobox(win, textvariable=sound_path, values=self.get_sound_files(), width=40).pack(pady=5)

        def update_alarm():
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            date_str = cal.get_date()
            time_str = time_entry.get()
            alarm_datetime = f"{date_str} {time_str}:00"
            cursor.execute("UPDATE alarm SET name=%s, sound_path=%s, alarm_time=%s WHERE id=%s",
                           (name_entry.get(), sound_path.get(), alarm_datetime, data[0]))
            conn.commit()
            conn.close()
            messagebox.showinfo("수정 완료", "알람이 수정되었습니다!")
            win.destroy()
            self.refresh_alarms()

        ttk.Button(win, text="수정", command=update_alarm).pack(pady=20)

    def delete_alarm(self):
        selected = self.tree.focus()
        if not selected:
            return
        if messagebox.askyesno("삭제 확인", "선택한 알람을 삭제하시겠습니까?"):
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alarm WHERE id=%s", (selected,))
            conn.commit()
            conn.close()
            self.refresh_alarms()

    def get_sound_files(self):
        folder = 'c:/alarm'
        if not os.path.exists(folder):
            os.makedirs(folder)
        return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.mp3')]

    def check_alarms(self):
        mixer.init()
        while True:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, sound_path, alarm_time FROM alarm")
            for alarm_id, name, sound, alarm_time in cursor.fetchall():
                if alarm_time.strftime('%Y-%m-%d %H:%M') == now:
                    notification.notify(title="⏰ 알람!", message=f"{name} - {alarm_time}", timeout=5)
                    self.play_sound_loop(sound)
            conn.close()
            time.sleep(30)

    def play_sound_loop(self, sound_path):
        def stop_sound():
            mixer.music.stop()
            stop_btn.destroy()

        sound_window = tk.Toplevel(self.root)
        sound_window.title("알람 재생 중")
        sound_window.geometry("300x150")

        ttk.Label(sound_window, text="🔔 알람이 울리는 중입니다!").pack(pady=20)
        stop_btn = ttk.Button(sound_window, text="알람 끄기", command=stop_sound)
        stop_btn.pack()

        while True:
            mixer.music.load(sound_path)
            mixer.music.play()
            while mixer.music.get_busy():
                time.sleep(1)

if __name__ == '__main__':
    root = tk.Tk()
    app = AlarmApp(root)
    root.mainloop()
