import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from winotify import Notification
from config import APP_NAME

def show_toast(title: str, message: str):
    toast = Notification(app_id= APP_NAME, title= title, msg= message)
    toast.show()

def show_notification(title: str, message: str):
    popup = PopupWindow(title)
    popup.set_text(message)
    popup.show()

class PopupWindow:
    def __init__(self, title="SMART Report", size="380x240"):
        self.root = tk.Tk()
        self.root.title(title)

        width, height = map(int, size.split("x"))

        # Bottom-right position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = screen_width - width - 20
        y = screen_height - height - 80

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.attributes("-topmost", True)

        # Optional: make it toast-like (no window frame)
        # self.root.overrideredirect(True)

        self.text = ScrolledText(self.root, wrap=tk.WORD)
        self.text.pack(expand=True, fill="both")

        # Auto close after 8 seconds
        self.root.after(8000, self.root.destroy)

    def set_text(self, content: str):
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, content)

    def show(self):
        self.root.mainloop()