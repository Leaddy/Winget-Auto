import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import subprocess
import threading
import re
import webbrowser

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class WingetUpdater(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Winget Güncelleme Yöneticisi")
        self.geometry("800x650") # Boyutu biraz artırdık

        # --- UI Düzeni ---
        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Başlıklar
        self.label_todo = ctk.CTkLabel(self, text="Güncellenecekler", font=("Arial", 14, "bold"))
        self.label_todo.grid(row=0, column=0, pady=10)

        self.label_skip = ctk.CTkLabel(self, text="Atlanacaklar", font=("Arial", 14, "bold"))
        self.label_skip.grid(row=0, column=2, pady=10)

        # Liste Kutuları
        self.list_todo = tk.Listbox(self, selectmode="multiple", bg="#2b2b2b", fg="white", borderwidth=0, highlightthickness=0, font=("Segoe UI", 10))
        self.list_todo.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.list_skip = tk.Listbox(self, selectmode="multiple", bg="#2b2b2b", fg="white", borderwidth=0, highlightthickness=0, font=("Segoe UI", 10))
        self.list_skip.grid(row=1, column=2, padx=20, pady=10, sticky="nsew")

        # Orta Kontrol Butonları
        self.frame_buttons = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_buttons.grid(row=1, column=1)

        self.btn_move_right = ctk.CTkButton(self.frame_buttons, text=">>", width=40, command=self.move_to_skip)
        self.btn_move_right.pack(pady=5)

        self.btn_move_left = ctk.CTkButton(self.frame_buttons, text="<<", width=40, command=self.move_to_todo)
        self.btn_move_left.pack(pady=5)

        # Alt Panel (Tarat, Başlat ve Progress)
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=20)

        self.btn_scan = ctk.CTkButton(self.bottom_frame, text="Tarat", command=self.scan_updates)
        self.btn_scan.pack(side="left", padx=10, pady=10)

        self.btn_start = ctk.CTkButton(self.bottom_frame, text="Güncellemeyi Başlat", fg_color="#28a745", hover_color="#218838", command=self.start_updates)
        self.btn_start.pack(side="right", padx=10, pady=10)

        self.credit_label = ctk.CTkLabel(
            self.bottom_frame, 
            text="coded by leaddy", 
            font=("Arial", 12, "italic"), 
            text_color="red",
            cursor="hand2" # Üzerine gelince el imleci çıkar
        )
        self.credit_label.pack(pady=(5, 0))
        # Tıklama olayını bağla
        self.credit_label.bind("<Button-1>", lambda e: webbrowser.open("https://linktr.ee/leaddy"))

        # Progress Bar ve Durum Etiketi
        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame, width=400)
        self.progress_bar.pack(pady=(10, 0), padx=20)
        self.progress_bar.set(0) # Başlangıçta boş

        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Durum: Hazır")
        self.status_label.pack(side="bottom", pady=5)

    def scan_updates(self):
        self.btn_scan.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate") # Tarama sırasında belirsiz mod
        self.progress_bar.start()
        
        self.status_label.configure(text="Durum: Winget taranıyor... Lütfen bekleyin.")
        
        self.list_todo.delete(0, tk.END)
        self.list_skip.delete(0, tk.END)
        
        def run_scan():
            try:
                # 'winget upgrade' komutunu çalıştır
                result = subprocess.run(['winget', 'upgrade'], capture_output=True, text=True, encoding='utf-8')
                lines = result.stdout.splitlines()
                
                exclude_keywords = ["upgrades available", "The following packages", "Name", "---", "ID", "Version"]
                found_start = False
                
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    if "---" in line:
                        found_start = True
                        continue
                    
                    if found_start:
                        if any(key in line for key in exclude_keywords):
                            continue
                        
                        # Birden fazla boşluğa göre böl (Ad, ID, Sürüm sütunları)
                        parts = re.split(r'\s{2,}', line)
                        if len(parts) > 0:
                            app_name = parts[0].strip()
                            if app_name:
                                self.list_todo.insert(tk.END, app_name)
                
                self.status_label.configure(text=f"Durum: Tarama tamamlandı. {self.list_todo.size()} güncelleme bulundu.")
            except Exception as e:
                self.status_label.configure(text=f"Hata: {str(e)}")
            finally:
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")
                self.progress_bar.set(0)
                self.btn_scan.configure(state="normal")
                self.btn_start.configure(state="normal")

        threading.Thread(target=run_scan, daemon=True).start()

    def move_to_skip(self):
        selected = list(self.list_todo.curselection())
        for i in reversed(selected):
            item = self.list_todo.get(i)
            self.list_skip.insert(tk.END, item)
            self.list_todo.delete(i)

    def move_to_todo(self):
        selected = list(self.list_skip.curselection())
        for i in reversed(selected):
            item = self.list_skip.get(i)
            self.list_todo.insert(tk.END, item)
            self.list_skip.delete(i)

    def start_updates(self):
        apps = self.list_todo.get(0, tk.END)
        if not apps:
            messagebox.showwarning("Uyarı", "Güncellenecek uygulama seçilmedi!")
            return

        self.btn_scan.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        
        total_apps = len(apps)
        self.progress_bar.set(0)

        def run_update():
            for index, app in enumerate(apps, 1):
                # UI Güncelleme
                self.status_label.configure(text=f"Durum: ({index}/{total_apps}) {app} güncelleniyor...")
                
                # Winget komutunu çalıştır
                # Not: --name bazen tam eşleşme istemeyebilir, --exact eklenebilir.
                subprocess.run(['winget', 'upgrade', '--name', app, '--silent', '--accept-package-agreements', '--accept-source-agreements'], capture_output=True)
                
                # Progress barı güncelle (0 ile 1 arasında değer alır)
                progress_value = index / total_apps
                self.progress_bar.set(progress_value)
            
            self.status_label.configure(text="Durum: Tüm işlemler tamamlandı!")
            self.btn_scan.configure(state="normal")
            self.btn_start.configure(state="normal")
            messagebox.showinfo("Başarılı", "Tüm güncellemeler tamamlandı!")

        threading.Thread(target=run_update, daemon=True).start()

if __name__ == "__main__":
    app = WingetUpdater()
    app.mainloop()