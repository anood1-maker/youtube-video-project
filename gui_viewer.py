import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd

class AntiBullyingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام كشف التنمر")
        self.root.geometry("900x600")

        # === Buttons ===
        tk.Button(root, text="📄 تحميل ملف نص الفيديو", command=self.load_transcription).pack(pady=5)
        tk.Button(root, text="💬 تحميل ملف التعليقات المصنفة", command=self.load_predictions).pack(pady=5)

        # === نسبة التنمر ===
        self.ratio_label = tk.Label(root, text="", font=("Arial", 12, "bold"), fg="darkred")
        self.ratio_label.pack(pady=5)

        # === نص الفيديو ===
        tk.Label(root, text="📝 نص الفيديو:", font=("Arial", 12, "bold")).pack()
        self.text_tree = ttk.Treeview(root, columns=("start", "end", "text"), show="headings", height=5)
        self.text_tree.pack(pady=5, fill=tk.X)
        self.text_tree.heading("start", text="من")
        self.text_tree.heading("end", text="إلى")
        self.text_tree.heading("text", text="النص")

        # === التعليقات ===
        tk.Label(root, text="💬 تعليقات اليوتيوب:", font=("Arial", 12, "bold")).pack()
        self.comments_tree = ttk.Treeview(root, columns=("comment", "prediction"), show="headings", height=10)
        self.comments_tree.pack(pady=5, fill=tk.BOTH, expand=True)
        self.comments_tree.heading("comment", text="التعليق")
        self.comments_tree.heading("prediction", text="التصنيف")

    def load_transcription(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)
            self.text_tree.delete(*self.text_tree.get_children())
            for _, row in df.iterrows():
                self.text_tree.insert("", "end", values=(row['start_time'], row['end_time'], row['text']))
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر قراءة ملف التفريغ:\n{e}")

    def load_predictions(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)
            self.comments_tree.delete(*self.comments_tree.get_children())

            total = len(df)
            bullying_count = len(df[df['prediction'] == 'تنمر'])
            ratio = (bullying_count / total) * 100 if total else 0
            self.ratio_label.config(text=f"📊 نسبة التنمر: {bullying_count} من {total} ({ratio:.2f}%)")

            for _, row in df.iterrows():
                self.comments_tree.insert("", "end", values=(row['comment'], row['prediction']))
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر قراءة ملف التعليقات:\n{e}")

# === تشغيل التطبيق ===
if __name__ == "__main__":
    root = tk.Tk()
    app = AntiBullyingApp(root)
    root.mainloop()
