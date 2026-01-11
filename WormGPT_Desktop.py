import tkinter as tk
from tkinter import ttk, messagebox, font
import requests
import json
import threading
from datetime import datetime
import webbrowser
import textwrap
import os
import uuid
import re

# ====== الإعدادات ======
APP_TITLE = "WormGPT Ultimate"
APP_VERSION = "2.3"
API_URL = "https://sii3.top/api/error/wormgpt.php"
API_KEY = "DarkAI-WormGPT-E487DD2FDAAEDC31A56A8A84"

# ====== الألوان (Modern Dark Theme) ======
COLORS = {
    'bg_main': '#1a1b26',
    'bg_sidebar': '#16161e',
    'bg_input': '#24283b',
    'user_bubble': '#7aa2f7',
    'ai_bubble': '#292e42',
    'text_main': '#c0caf5',
    'text_user': '#1a1b26',
    'text_ai': '#c0caf5',
    'code_bg': '#15161e',  # Darker for code
    'code_fg': '#73daca',  # Cyan-ish for code
    'accent': '#bb9af7',
    'button': '#7aa2f7',
    'button_hover': '#89b4fa',
    'scroll': '#414868',
    'sidebar_hover': '#2f354b',
    'sidebar_selected': '#3b4261',
    'danger': '#f7768e',
    'success': '#9ece6a'
}

# ====== Global Settings ======
SETTINGS = {
    'font_size': 10
}

class ChatManager:
    def __init__(self, filename="chats.json"):
        self.filename = filename
        self.chats = {}
        self.current_chat_id = None
        self.load_chats()

    def load_chats(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.chats = data.get('chats', {})
                    self.current_chat_id = data.get('current_chat_id')
                    global SETTINGS
                    SETTINGS.update(data.get('settings', {}))
            except:
                self.chats = {}
                self.current_chat_id = None
        
        if not self.chats:
            self.create_new_chat()
        elif self.current_chat_id not in self.chats:
            self.current_chat_id = list(self.chats.keys())[0]

    def save_chats(self):
        data = {
            'current_chat_id': self.current_chat_id,
            'settings': SETTINGS,
            'chats': self.chats
        }
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_new_chat(self):
        chat_id = str(uuid.uuid4())
        self.chats[chat_id] = {
            'title': 'محادثة جديدة',
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
        self.current_chat_id = chat_id
        self.save_chats()
        return chat_id

    def delete_chat(self, chat_id):
        if chat_id in self.chats:
            del self.chats[chat_id]
            if self.current_chat_id == chat_id:
                self.current_chat_id = None
                if self.chats:
                    self.current_chat_id = list(self.chats.keys())[0]
                else:
                    self.create_new_chat()
            self.save_chats()
            return True
        return False

    def add_message(self, role, content, timestamp):
        if self.current_chat_id and self.current_chat_id in self.chats:
            self.chats[self.current_chat_id]['messages'].append({
                'role': role,
                'content': content,
                'timestamp': timestamp
            })
            
            msgs = self.chats[self.current_chat_id]['messages']
            user_msgs = [m for m in msgs if m['role'] == 'user']
            if len(user_msgs) == 1 and role == 'user':
                title = content[:25] + "..." if len(content) > 25 else content
                self.chats[self.current_chat_id]['title'] = title
            
            self.save_chats()

    def get_messages(self):
        if self.current_chat_id and self.current_chat_id in self.chats:
            return self.chats[self.current_chat_id]['messages']
        return []

    def get_history_context(self, limit=6):
        if not self.current_chat_id: return ""
        msgs = self.get_messages()
        history = msgs[-(limit+1):-1] 
        formatted = ""
        for m in history:
            role = "User" if m['role'] == 'user' else "Assistant"
            formatted += f"{role}: {m['content']}\n"
        return formatted

class CodeBlock(tk.Frame):
    def __init__(self, master, code_content):
        super().__init__(master, bg=COLORS['code_bg'], bd=1, relief='solid')
        self.code_content = code_content
        
        # Header (Copy Button)
        header = tk.Frame(self, bg='#1f2335', height=25)
        header.pack(fill='x')
        
        tk.Label(header, text="Code", fg='#565f89', bg='#1f2335', font=("Consolas", 8)).pack(side='left', padx=5)
        
        copy_btn = tk.Button(header, text="📋 نسخ الكود", command=self.copy_code,
                           bg='#1f2335', fg=COLORS['text_main'], font=("Segoe UI", 8),
                           relief='flat', activebackground='#1f2335', activeforeground='white',
                           cursor='hand2', bd=0)
        copy_btn.pack(side='right', padx=5)
        
        # Code Content
        font_size = SETTINGS.get('font_size', 10)
        self.text_widget = tk.Text(self, height=len(code_content.split('\n')), width=50,
                                 bg=COLORS['code_bg'], fg=COLORS['code_fg'],
                                 font=("Consolas", font_size), relief='flat', padx=10, pady=10)
        self.text_widget.insert('1.0', code_content)
        self.text_widget.configure(state='disabled')
        self.text_widget.pack(fill='both', expand=True)

    def copy_code(self):
        self.clipboard_clear()
        self.clipboard_append(self.code_content)
        messagebox.showinfo("تم النسخ", "✅ تم نسخ الكود بنجاح!")

class ChatBubble(tk.Frame):
    def __init__(self, master, message, is_user=True, timestamp="", width=400):
        super().__init__(master, bg=COLORS['bg_main'])
        self.is_user = is_user
        self.width = width
        
        # Determine colors and alignment
        bg_color = COLORS['user_bubble'] if is_user else COLORS['ai_bubble']
        fg_color = COLORS['text_user'] if is_user else COLORS['text_ai']
        
        # RTL Logic: If first char is Arabic, align right
        is_rtl = False
        if message.strip():
            first_char = message.strip()[0]
            if '\u0600' <= first_char <= '\u06FF':
                is_rtl = True
        
        align = 'e' if (is_user or is_rtl) else 'w'
        txt_anchor = 'e' if is_rtl else 'w'
        txt_justify = 'right' if is_rtl else 'left'
        
        # Main Container with rounded look
        self.container = tk.Frame(self, bg=bg_color, padx=10, pady=10)
        self.container.pack(anchor=align, padx=10, pady=5, fill=None)
        
        # Parse Message for Code Blocks
        parts = re.split(r"```", message)
        font_size = SETTINGS.get('font_size', 10)
        
        for i, part in enumerate(parts):
            if i % 2 == 1: # This is a code block
                if part.strip():
                    code = CodeBlock(self.container, part.strip())
                    code.pack(fill='x', pady=5, anchor='w')
            else: # This is text
                if part.strip():
                    lbl = tk.Label(self.container, text=part.strip(), 
                                 bg=bg_color, fg=fg_color, 
                                 font=("Segoe UI", font_size), justify=txt_justify, anchor=txt_anchor,
                                 wraplength=int(width*0.8))
                    lbl.pack(anchor=txt_anchor, fill='x')

        # Footer (Time + Copy All)
        footer = tk.Frame(self.container, bg=bg_color)
        footer.pack(fill='x', pady=(5, 0))
        
        time_lbl = tk.Label(footer, text=timestamp, bg=bg_color, fg='#565f89', font=("Segoe UI", 8))
        time_lbl.pack(side='right' if is_user else 'left')
        
        copy_btn = tk.Label(footer, text="📋", bg=bg_color, fg='#565f89', cursor='hand2')
        copy_btn.pack(side='left' if is_user else 'right', padx=5)
        copy_btn.bind("<Button-1>", lambda e: self.copy_all(message))

    def copy_all(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("تم النسخ", "تم نسخ الرسالة كاملة.")

class ModernWormGPT:
    def __init__(self, root):
        self.chat_manager = ChatManager()
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry("1100x800")
        self.root.configure(bg=COLORS['bg_main'])
        self.is_processing = False
        
        self.setup_ui()
        self.load_current_chat()
        
        self.root.bind_all("<MouseWheel>", self.on_mousewheel)
        self.root.bind_all("<Button-4>", self.on_mousewheel)
        self.root.bind_all("<Button-5>", self.on_mousewheel)

    def setup_ui(self):
        # === Sidebar ===
        self.sidebar = tk.Frame(self.root, bg=COLORS['bg_sidebar'], width=250)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="المحادثات", font=("Segoe UI", 14, "bold"), 
                 bg=COLORS['bg_sidebar'], fg='white').pack(pady=(20, 10))
                 
        tk.Button(self.sidebar, text="+ محادثة جديدة", command=self.new_chat,
                  bg=COLORS['button'], fg=COLORS['text_user'], font=("Segoe UI", 10, "bold"),
                  relief='flat', cursor='hand2').pack(fill='x', padx=15, pady=10)
                  
        self.chat_list_frame = tk.Frame(self.sidebar, bg=COLORS['bg_sidebar'])
        self.chat_list_frame.pack(fill='both', expand=True, padx=5)
        
        # Settings Button
        tk.Button(self.sidebar, text="⚙️ الإعدادات", command=self.open_settings,
                  bg=COLORS['bg_input'], fg='white', relief='flat').pack(side='bottom', fill='x', padx=20, pady=20)

        # === Main Content ===
        self.main_area = tk.Frame(self.root, bg=COLORS['bg_main'])
        self.main_area.pack(side='right', fill='both', expand=True)
        
        # Header
        self.header = tk.Frame(self.main_area, bg=COLORS['bg_main'], height=60)
        self.header.pack(fill='x')
        self.header.pack_propagate(False)
        
        tk.Label(self.header, text=APP_TITLE, font=("Segoe UI", 16, "bold"), 
                 bg=COLORS['bg_main'], fg=COLORS['accent']).pack(side='left', padx=20, pady=10)
        
        # Info Button (Restored)
        info_btn = tk.Button(self.header, text="ℹ️ معلومات المطور", command=self.show_about,
                           bg=COLORS['bg_input'], fg='white', relief='flat', font=("Segoe UI", 9))
        info_btn.pack(side='right', padx=5)
                 
        # Status Label
        self.status_var = tk.StringVar(value="متصل ✅")
        self.status_lbl = tk.Label(self.header, textvariable=self.status_var, 
                                 bg=COLORS['bg_main'], fg=COLORS['success'], font=("Segoe UI", 9))
        self.status_lbl.pack(side='right', padx=15)

        # Chat Area (Scrollable Frame)
        self.chat_canvas = tk.Canvas(self.main_area, bg=COLORS['bg_main'], highlightthickness=0)
        self.chat_scrollbar = ttk.Scrollbar(self.main_area, orient="vertical", command=self.chat_canvas.yview)
        
        self.chat_frame = tk.Frame(self.chat_canvas, bg=COLORS['bg_main'])
        self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)
        self.chat_canvas.pack(side="top", fill="both", expand=True)
        self.chat_scrollbar.place(relx=1, rely=0.1, relheight=0.8, anchor="ne")
        
        self.chat_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig(self.chat_window, width=e.width))

        # Input
        self.input_container = tk.Frame(self.main_area, bg=COLORS['bg_sidebar'], height=90)
        self.input_container.pack(fill='x', side='bottom')
        
        self.input_field = tk.Text(self.input_container, height=3, bg=COLORS['bg_input'], 
                                 fg='white', font=("Segoe UI", 11), relief='flat', insertbackground='white')
        self.input_field.pack(side='left', fill='both', expand=True, padx=20, pady=15)
        self.input_field.bind("<Return>", self.on_enter)
        
        # Explicit Paste Bindings
        self.input_field.bind("<Control-v>", lambda e: self.custom_paste())
        self.input_field.bind("<Control-V>", lambda e: self.custom_paste())
        
        self.send_btn = tk.Button(self.input_container, text="إرسال", command=self.send_message,
                                bg=COLORS['button'], fg=COLORS['text_user'], font=("Segoe UI", 10, "bold"),
                                relief='flat', padx=15)
        self.send_btn.pack(side='right', padx=20, pady=15)

    def refresh_chat_list(self):
        for widget in self.chat_list_frame.winfo_children(): widget.destroy()
        sorted_chats = sorted(self.chat_manager.chats.items(), key=lambda x: x[1].get('created_at', ''), reverse=True)
        for chat_id, data in sorted_chats:
            bg = COLORS['sidebar_selected'] if chat_id == self.chat_manager.current_chat_id else COLORS['bg_sidebar']
            # RTL Alignment for titles if they contain Arabic
            title_text = data['title']
            btn_anchor = 'e' if any('\u0600' <= c <= '\u06FF' for c in title_text) else 'w'
            
            btn = tk.Button(self.chat_list_frame, text=title_text, anchor=btn_anchor, bg=bg, fg='white',
                          relief='flat', padx=10, pady=5, cursor='hand2', justify='right' if btn_anchor == 'e' else 'left',
                          command=lambda cid=chat_id: self.switch_chat(cid))
            btn.pack(fill='x', pady=1)

    def switch_chat(self, chat_id):
        if self.is_processing: return
        self.chat_manager.current_chat_id = chat_id
        self.chat_manager.save_chats()
        self.load_current_chat()

    def new_chat(self):
        if self.is_processing: return
        self.chat_manager.create_new_chat()
        self.load_current_chat()

    def load_current_chat(self):
        for widget in self.chat_frame.winfo_children(): widget.destroy()
        self.refresh_chat_list()
        msgs = self.chat_manager.get_messages()
        if not msgs:
            self.add_bubble("مرحباً! كيف يمكنني مساعدتك؟", False, datetime.now().strftime("%H:%M"))
        else:
            for m in msgs:
                self.add_bubble(m['content'], m['role'] == 'user', m['timestamp'])

    def add_bubble(self, message, is_user, timestamp):
        bubble = ChatBubble(self.chat_frame, message, is_user, timestamp, width=self.main_area.winfo_width())
        bubble.pack(fill='x', padx=10, pady=5)
        self.root.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
        
    def on_enter(self, event):
        if not event.state & 1: self.send_message(); return "break"

    def send_message(self):
        msg = self.input_field.get("1.0", "end-1c").strip()
        if not msg or self.is_processing: return
        
        timestamp = datetime.now().strftime("%H:%M")
        self.input_field.delete("1.0", "end")
        self.add_bubble(msg, True, timestamp)
        self.chat_manager.add_message('user', msg, timestamp)
        self.refresh_chat_list()
        
        self.is_processing = True
        self.send_btn.config(state='disabled')
        self.status_var.set("WormGPT يكتب... ✍️")
        
        threading.Thread(target=self.process_ai, args=(msg,), daemon=True).start()

    def process_ai(self, user_msg):
        try:
            context = self.chat_manager.get_history_context(limit=8)
            system_prompt = f"""
            Instructions:
            1. Answer in Arabic language ONLY.
            2. Format code blocks using ```language ```.
            3. Be helpful and accurate.
            
            Conversation History:
            {context}
            
            User Message: {user_msg}
            
            Assistant Response (in Arabic):
            """
            response = requests.post(API_URL, data={'key': API_KEY, 'text': system_prompt}, timeout=45)
            reply = response.json().get("response", "⚠️ Error") if response.status_code == 200 else "❌ Connection Error"
            self.root.after(0, self.finish_ai_response, reply)
        except Exception as e:
            self.root.after(0, self.finish_ai_response, f"❌ Error: {str(e)}")

    def finish_ai_response(self, reply):
        timestamp = datetime.now().strftime("%H:%M")
        self.add_bubble(reply, False, timestamp)
        self.chat_manager.add_message('ai', reply, timestamp)
        self.is_processing = False
        self.send_btn.config(state='normal')
        self.status_var.set("متصل ✅")

    def on_mousewheel(self, event):
        if event.num == 5 or event.delta < 0: self.chat_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0: self.chat_canvas.yview_scroll(-1, "units")

    def custom_paste(self):
        try:
            text = self.root.clipboard_get()
            self.input_field.insert(tk.INSERT, text)
        except:
            pass
        return "break"

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("الإعدادات")
        win.geometry("300x250")
        win.configure(bg=COLORS['bg_main'])
        
        tk.Label(win, text="حجم الخط", bg=COLORS['bg_main'], fg='white').pack(pady=10)
        
        def set_font(size):
            SETTINGS['font_size'] = size
            self.chat_manager.save_chats()
            self.load_current_chat() # Reload to apply
            
        frame = tk.Frame(win, bg=COLORS['bg_main'])
        frame.pack()
        tk.Button(frame, text="صغير", command=lambda: set_font(9)).pack(side='left', padx=5)
        tk.Button(frame, text="متوسط", command=lambda: set_font(11)).pack(side='left', padx=5)
        tk.Button(frame, text="كبير", command=lambda: set_font(13)).pack(side='left', padx=5)
        
        tk.Label(win, text="منطقة الخطر", bg=COLORS['bg_main'], fg=COLORS['danger']).pack(pady=(30, 10))
        tk.Button(win, text="حذف جميع البيانات", bg=COLORS['danger'], fg='white',
                command=lambda: self.reset_data(win)).pack()

    def reset_data(self, win):
        if messagebox.askyesno("تحذير", "سيتم حذف كل المحادثات! هل أنت متأكد؟"):
            self.chat_manager.chats = {}
            self.chat_manager.create_new_chat()
            self.chat_manager.save_chats()
            self.load_current_chat()
            win.destroy()

    def show_about(self):
        about = tk.Toplevel(self.root)
        about.title("معلومات المطور")
        about.geometry("400x350")
        about.configure(bg=COLORS['bg_main'])
        
        tk.Label(about, text="WormGPT Pro", font=("Segoe UI", 16, "bold"), 
                 bg=COLORS['bg_main'], fg=COLORS['accent']).pack(pady=20)
        
        def link(text, url):
            l = tk.Label(about, text=text, fg=COLORS['button'], bg=COLORS['bg_main'], 
                         cursor="hand2", font=("Segoe UI", 11, "underline"))
            l.pack(pady=5)
            l.bind("<Button-1>", lambda e: webbrowser.open(url))
            
        tk.Label(about, text="المطور:", bg=COLORS['bg_main'], fg='white').pack()
        link("@Sul4384", "https://t.me/Sul4384")
        
        tk.Label(about, text="\nالقناة الرسمية:", bg=COLORS['bg_main'], fg='white').pack()
        link("@SAM_CYS", "https://t.me/SAM_CYS")
        
        tk.Button(about, text="إغلاق", command=about.destroy, bg=COLORS['button'], fg='white').pack(pady=30)

if __name__ == "__main__":
    if not os.path.exists("chats.json"):
        with open("chats.json", "w") as f: json.dump({}, f)
    root = tk.Tk()
    app = ModernWormGPT(root)
    root.mainloop()
