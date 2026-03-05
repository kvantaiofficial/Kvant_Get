import os
import threading
from io import BytesIO
from tkinter import filedialog, messagebox
import tkinter as tk
import customtkinter as ctk
import requests
import yt_dlp
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

GREEN = "#00FF41"
GREEN_LIGHT = "#39FF14"
BG_MAIN = "#0D0D0D"
BG_BAR = "#141414"
BG_ENTRY = "#1A1A1A"
BG_THUMB = "#050505"
GREY_DIM = "#006400"
GREY_PATH = "#3A3A3A"
THUMB_W, THUMB_H = 320, 180

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("KVANT GET")
        self.geometry("900x530")
        self.minsize(750, 460)
        self.configure(fg_color=BG_MAIN)
        
        icon_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        icon_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        
        if os.path.exists(icon_ico):
            try:
                self.iconbitmap(icon_ico)
            except: pass
        
        if os.path.exists(icon_png):
            try:
                self.after(200, lambda: self.iconphoto(False, tk.PhotoImage(file=icon_png)))
            except: pass

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.video_info = None
        self._fetch_url = ""
        self._thumb_ref = None
        self._build()

    def _build(self):
        self._build_top()
        self._build_bar()

    def _build_top(self):
        self._top = ctk.CTkFrame(self, fg_color=BG_MAIN)
        self._top.pack(side="top", fill="both", expand=True)
        col = ctk.CTkFrame(self._top, fg_color=BG_MAIN)
        col.place(relx=0.5, rely=0.5, anchor="center")
        thumb_border = ctk.CTkFrame(col, fg_color="#1E1E1E", corner_radius=6, border_width=0)
        thumb_border.pack()
        thumb_inner = tk.Frame(thumb_border, bg=BG_THUMB, width=THUMB_W, height=THUMB_H)
        thumb_inner.pack(padx=1, pady=1)
        thumb_inner.pack_propagate(False)
        self._thumb_lbl = tk.Label(thumb_inner, text="[ NO SIGNAL ]", bg=BG_THUMB, fg=GREY_DIM, font=("Consolas", 11))
        self._thumb_lbl.pack(expand=True)
        self._title_lbl = ctk.CTkLabel(col, text="Awaiting Video Stream...", font=("Consolas", 14, "italic"), text_color=GREEN, wraplength=640)
        self._title_lbl.pack(pady=(12, 2))
        self._status_lbl = ctk.CTkLabel(col, text="System Ready", font=("Consolas", 10), text_color=GREY_DIM)
        self._status_lbl.pack()

    def _build_bar(self):
        sep = tk.Frame(self, bg="#222222", height=1)
        sep.pack(side="bottom", fill="x")
        self._path_lbl = ctk.CTkLabel(self, text=f"SAVE TO: {self.save_path}", font=("Consolas", 9), text_color=GREY_PATH, anchor="w")
        self._path_lbl.pack(side="bottom", fill="x", padx=24, pady=(0, 3))
        bar = ctk.CTkFrame(self, fg_color=BG_BAR, corner_radius=0, height=108)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        self._folder_btn = ctk.CTkButton(bar, text="🗁", width=46, height=46, fg_color="#1E1E1E", hover_color="#2A2A2A", text_color=GREEN, font=("Segoe UI Emoji", 20), border_width=1, border_color="#2A2A2A", corner_radius=6, command=self._select_folder)
        self._folder_btn.pack(side="left", padx=(20, 10), pady=31)
        center = ctk.CTkFrame(bar, fg_color="transparent")
        center.pack(side="left", fill="both", expand=True, padx=6, pady=24)
        entry_container = ctk.CTkFrame(center, fg_color=BG_ENTRY, height=42, border_color="#2C2C2C", border_width=1, corner_radius=6)
        entry_container.pack(fill="x", pady=(0, 8))
        entry_container.pack_propagate(False)
        self._url_entry = tk.Entry(entry_container, bg=BG_ENTRY, fg=GREEN_LIGHT, insertbackground=GREEN, relief="flat", bd=0, font=("Consolas", 13), selectbackground="#004400", selectforeground=GREEN_LIGHT)
        self._url_entry.pack(fill="both", expand=True, padx=10, pady=5)
        self._url_entry.insert(0, "PASTE OR TYPE LINK...")
        self._url_entry.bind("<FocusIn>", lambda e: self._handle_focus_in())
        self._url_entry.bind("<FocusOut>", lambda e: self._handle_focus_out())
        self._url_entry.bind("<KeyRelease>", lambda e: self._trigger_fetch())
        self.bind_all("<Control-v>", lambda e: self.after(1, self._paste))
        self.bind_all("<Control-V>", lambda e: self.after(1, self._paste))
        _menu = tk.Menu(self, tearoff=0, bg="#1E1E1E", fg=GREEN, activebackground=GREEN, activeforeground="black", font=("Consolas", 10), bd=0)
        _menu.add_command(label="PASTE", command=self._paste)
        _menu.add_command(label="CLEAR", command=self._clear)
        self._url_entry.bind("<Button-3>", lambda e: _menu.post(e.x_root, e.y_root))
        self._btn_paste = ctk.CTkButton(bar, text="PASTE", width=80, height=42, fg_color="#1E1E1E", hover_color="#2A2A2A", text_color=GREEN_LIGHT, font=("Consolas", 11, "bold"), border_width=1, border_color="#2C2C2C", command=self._paste)
        self._btn_paste.pack(side="right", padx=(5, 10), pady=31, before=center)
        self._prog = ctk.CTkProgressBar(center, fg_color="#111111", progress_color=GREEN, height=4, corner_radius=2)
        self._prog.set(0)
        self._prog.pack(fill="x")
        self._dl_btn = ctk.CTkButton(bar, text="▶ DOWNLOAD", font=("Consolas", 15, "bold"), fg_color=GREEN, hover_color=GREEN_LIGHT, text_color="#000000", width=185, height=52, corner_radius=8, state="disabled", command=self._start_download)
        self._dl_btn.pack(side="right", padx=(10, 20), pady=28)

    def _handle_focus_in(self):
        if self._url_entry.get() == "PASTE OR TYPE LINK...":
            self._url_entry.delete(0, "end")

    def _handle_focus_out(self):
        if not self._url_entry.get():
            self._url_entry.insert(0, "PASTE OR TYPE LINK...")

    def _paste(self):
        try:
            text = self.clipboard_get()
        except:
            try:
                text = self.selection_get(selection='CLIPBOARD')
            except:
                return
        if text:
            clean_text = str(text).strip()
            if self._url_entry.get() == "PASTE OR TYPE LINK...":
                self._url_entry.delete(0, "end")
            self._url_entry.delete(0, "end")
            self._url_entry.insert(0, clean_text)
            self._trigger_fetch()

    def _clear(self):
        self._url_entry.delete(0, "end")
        self._handle_focus_out()
        self._reset()

    def _trigger_fetch(self):
        url = self._url_entry.get().strip()
        if url.startswith("http") and url != self._fetch_url:
            self._fetch_url = url
            threading.Thread(target=self._fetch_meta, args=(url,), daemon=True).start()
        elif not url.startswith("http"):
            self._reset()

    def _fetch_meta(self, url):
        self.after(0, lambda: self._set_status("DECRYPTING URL..."))
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            title = info.get("title", "Unknown")
            thumb_url = info.get("thumbnail", "")
            self.video_info = info
            tk_img = None
            if thumb_url:
                data = requests.get(thumb_url, timeout=10).content
                img = Image.open(BytesIO(data))
                w, h = img.size
                ratio = min(THUMB_W / w, THUMB_H / h)
                new_sz = (int(w * ratio), int(h * ratio))
                img = img.resize(new_sz, Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
            self.after(0, lambda: self._show(title, tk_img))
        except:
            self.after(0, self._on_error)

    def _show(self, title, tk_img):
        self._title_lbl.configure(text=title)
        if tk_img:
            self._thumb_ref = tk_img
            self._thumb_lbl.config(image=tk_img, text="", compound="none")
        self._dl_btn.configure(state="normal")
        self._set_status("SIGNAL ESTABLISHED")

    def _on_error(self):
        self._set_status("ACCESS DENIED / INVALID LINK")
        self._title_lbl.configure(text="SIGNAL LOST")
        self._thumb_lbl.config(image="", compound="none", text="[ ERROR ]")
        self._dl_btn.configure(state="disabled")

    def _reset(self):
        self.video_info = None
        self._fetch_url = ""
        self._thumb_ref = None
        self._thumb_lbl.config(image="", compound="none", text="[ NO SIGNAL ]")
        self._title_lbl.configure(text="Awaiting Video Stream...")
        self._dl_btn.configure(state="disabled")
        self._prog.set(0)

    def _select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path = path
            self._path_lbl.configure(text=f"SAVE TO: {self.save_path}")

    def _set_status(self, msg):
        self._status_lbl.configure(text=f"> {msg}")

    def _start_download(self):
        url = self._url_entry.get().strip()
        if not url or url == "PASTE OR TYPE LINK...":
            return
        self._dl_btn.configure(state="disabled", text="LOADING...")
        self._set_status("INITIALIZING...")
        self._prog.set(0)
        threading.Thread(target=self._download, args=(url,), daemon=True).start()

    def _download(self, url):
        def hook(d):
            if d["status"] == "downloading":
                try:
                    total = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
                    done = d.get("downloaded_bytes", 0)
                    p = done / total
                    self.after(0, lambda: self._prog.set(p))
                    self.after(0, lambda: self._set_status(f"DOWNLOADING... {int(p * 100)}%"))
                except:
                    pass
        opts = {"format": "best", "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"), "progress_hooks": [hook], "quiet": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.after(0, self._done)
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("Error", str(exc)))
            self.after(0, lambda: self._dl_btn.configure(state="normal", text="▶ DOWNLOAD"))

    def _done(self):
        self._set_status("TASK COMPLETE")
        self._prog.set(1)
        self._dl_btn.configure(state="normal", text="▶ DOWNLOAD")
        messagebox.showinfo("KVANT.GET", "Data transfer complete.")

if __name__ == "__main__":
    App().mainloop()
