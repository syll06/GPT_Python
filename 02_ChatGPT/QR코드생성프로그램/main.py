import os
import uuid
import qrcode
import mysql.connector
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

# =============================
# Database Setup
# =============================
def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="python",
        password="123456",
        database="python"
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS qr_code (
        no INT AUTO_INCREMENT PRIMARY KEY,
        id VARCHAR(36) NOT NULL,
        name VARCHAR(255) NOT NULL,
        value TEXT NOT NULL,
        path TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )''')
    conn.commit()
    return conn

# =============================
# QR Code Logic
# =============================
def generate_qr_code(name, value, save_path):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{now}_{name}.png"
    file_path = os.path.join(save_path, filename)

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(value)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    img.save(file_path)
    return file_path

# =============================
# GUI Program
# =============================
class QRCodeApp:
    def __init__(self, root):
        self.conn = init_db()
        self.cursor = self.conn.cursor()

        root.title("QR 코드 생성 & 관리 프로그램")
        root.geometry("750x500")

        self.tabControl = ttk.Notebook(root)

        self.create_tab = ttk.Frame(self.tabControl)
        self.manage_tab = ttk.Frame(self.tabControl)

        self.tabControl.add(self.create_tab, text='QR 코드 생성')
        self.tabControl.add(self.manage_tab, text='QR 코드 관리')
        self.tabControl.pack(expand=1, fill="both")

        self.setup_create_tab()
        self.setup_manage_tab()

    # -----------------------------
    # QR 코드 생성 탭
    # -----------------------------
    def setup_create_tab(self):
        tk.Label(self.create_tab, text="QR 코드 이름:").pack(pady=5)
        self.qr_name_entry = tk.Entry(self.create_tab, width=50)
        self.qr_name_entry.pack()

        tk.Label(self.create_tab, text="QR 코드 값:").pack(pady=5)
        self.qr_value_entry = tk.Entry(self.create_tab, width=50)
        self.qr_value_entry.pack()

        tk.Label(self.create_tab, text="저장 경로:").pack(pady=5)
        self.path_entry = tk.Entry(self.create_tab, width=50)
        self.path_entry.pack()

        tk.Button(self.create_tab, text="경로 선택", command=self.select_path).pack(pady=5)
        tk.Button(self.create_tab, text="QR 코드 생성", command=self.create_qr_code).pack(pady=10)

    def select_path(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)

    def create_qr_code(self):
        name = self.qr_name_entry.get()
        value = self.qr_value_entry.get()
        path = self.path_entry.get()

        if not (name and value and path):
            messagebox.showerror("오류", "모든 항목을 입력해주세요.")
            return

        file_path = generate_qr_code(name, value, path)
        qr_id = str(uuid.uuid4())

        sql = "INSERT INTO qr_code (id, name, value, path) VALUES (%s, %s, %s, %s)"
        self.cursor.execute(sql, (qr_id, name, value, file_path))
        self.conn.commit()

        messagebox.showinfo("성공", f"QR 코드가 생성되었습니다.\n파일 경로: {file_path}")
        self.load_qr_list()

    # -----------------------------
    # QR 코드 관리 탭
    # -----------------------------
    def setup_manage_tab(self):
        self.tree = ttk.Treeview(self.manage_tab, columns=("no", "name", "value", "path", "created_at"), show='headings')
        self.tree.heading("no", text="번호")
        self.tree.heading("name", text="이름")
        self.tree.heading("value", text="코드 값")
        self.tree.heading("path", text="경로")
        self.tree.heading("created_at", text="등록일자")

        self.tree.column("no", width=50)
        self.tree.column("name", width=100)
        self.tree.column("value", width=180)
        self.tree.column("path", width=200)
        self.tree.column("created_at", width=120)

        self.tree.pack(expand=True, fill='both')

        btn_frame = tk.Frame(self.manage_tab)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="이름 변경", command=self.rename_qr).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="삭제", command=self.delete_qr).grid(row=0, column=1, padx=5)

        self.load_qr_list()

    def load_qr_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT no, name, value, path, created_at FROM qr_code ORDER BY no DESC")
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def rename_qr(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("오류", "수정할 QR 코드를 선택하세요.")
            return

        values = self.tree.item(selected, 'values')
        new_name = tk.simpledialog.askstring("이름 변경", f"새 이름을 입력하세요 (현재: {values[1]})")
        if new_name:
            self.cursor.execute("UPDATE qr_code SET name=%s WHERE no=%s", (new_name, values[0]))
            self.conn.commit()
            messagebox.showinfo("성공", "이름이 변경되었습니다.")
            self.load_qr_list()

    def delete_qr(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("오류", "삭제할 QR 코드를 선택하세요.")
            return

        values = self.tree.item(selected, 'values')
        confirm = messagebox.askyesno("확인", f"{values[1]} QR 코드를 삭제하시겠습니까?")
        if confirm:
            # 파일 삭제
            try:
                if os.path.exists(values[3]):
                    os.remove(values[3])
            except Exception as e:
                messagebox.showwarning("경고", f"파일 삭제 중 오류 발생: {e}")

            # DB 삭제
            self.cursor.execute("DELETE FROM qr_code WHERE no=%s", (values[0],))
            self.conn.commit()
            messagebox.showinfo("성공", "QR 코드가 삭제되었습니다.")
            self.load_qr_list()

# =============================
# 실행
# =============================
if __name__ == "__main__":
    root = tk.Tk()
    app = QRCodeApp(root)
    root.mainloop()
