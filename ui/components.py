"""Apple NotesスタイリングのTodoアプリケーション用UI Components"""
import tkinter as tk
from tkinter import messagebox
from style.theme import Theme


# ============================================================================
#  Widgets
# ============================================================================

class AppleButton(tk.Button):
    """Apple Notesスタイリングとホバー効果を持つbutton """
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            bg=Theme.Color.BUTTON_BG,
            fg=Theme.Color.TEXT,
            font=Theme.Font.get(),
            activebackground=Theme.Color.BUTTON_HOVER,
            activeforeground=Theme.Color.TEXT,
            relief="flat",
            borderwidth=0,
            padx=Theme.Layout.PADDING_X,
            pady=Theme.Layout.PADDING_Y
        )
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)

    def _on_hover(self, event):
        """hover効果を処理 """
        self.configure(bg=Theme.Color.BUTTON_HOVER, cursor="hand2")

    def _on_leave(self, event):
        """マウス離脱効果を処理 """
        self.configure(bg=Theme.Color.BUTTON_BG, cursor="")


class AppleEntry(tk.Entry):
    """Apple Notesスタイリングのentry field """
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            bg=Theme.Color.ENTRY_BG,
            fg=Theme.Color.TEXT,
            relief="flat",
            font=Theme.Font.get(),
            insertbackground=Theme.Color.TEXT,
            highlightthickness=1,
            highlightbackground=Theme.Color.BORDER,
            highlightcolor=Theme.Color.BORDER_FOCUS,
            bd=Theme.Layout.BORDER_WIDTH
        )


class AppleRadiobutton(tk.Radiobutton):
    """Apple Notesスタイリングのradio button """
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            bg=Theme.Color.BACKGROUND,
            fg=Theme.Color.TEXT,
            activebackground=Theme.Color.BACKGROUND,
            activeforeground=Theme.Color.TEXT,
            selectcolor=Theme.Color.BACKGROUND,
            font=Theme.Font.get(),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=6,
            pady=4,
            anchor="w"
        )


# ============================================================================
#  Modal
# ============================================================================

class ConfirmDialog(tk.Toplevel):
    """windowの中央に表示 """

    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.result = False

        # Window設定 
        self.title(title)
        self.configure(bg=Theme.Color.BACKGROUND)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # UIを作成 
        main_frame = tk.Frame(self, bg=Theme.Color.BACKGROUND, padx=30, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Message label
        label = tk.Label(
            main_frame,
            text=message,
            font=Theme.Font.get(),
            bg=Theme.Color.BACKGROUND,
            fg=Theme.Color.TEXT,
            wraplength=300,
            justify="center"
        )
        label.pack(pady=(0, 25), expand=True, fill=tk.BOTH)

        # Buttons
        button_frame = tk.Frame(main_frame, bg=Theme.Color.BACKGROUND)
        button_frame.pack()

        self.confirm_button = AppleButton(button_frame, text="确定", width=8, command=self._on_confirm)
        self.confirm_button.pack(side=tk.LEFT, padx=10)

        self.cancel_button = AppleButton(button_frame, text="キャンセル", width=8, command=self._on_cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=10)


        # 中央表示
        self._center_on_parent()
        self.wait_window(self)

    def _center_on_parent(self):
        """windowの中央に配置 """
        self.update_idletasks()
        
        parent = self.master
        parent_x, parent_y = parent.winfo_x(), parent.winfo_y()
        parent_w, parent_h = parent.winfo_width(), parent.winfo_height()
        dialog_w, dialog_h = self.winfo_width(), self.winfo_height()
        
        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2
        
        self.geometry(f"+{x}+{y}")

    def _on_confirm(self):
        self.result = True
        self.destroy()

    def _on_cancel(self):
        self.result = False
        self.destroy()


# ============================================================================
# 便利関数 / Convenience Functions
# ============================================================================

def show_confirm(parent, title="确认", message="确定要执行此操作吗？"):
    """確認dialogを表示、ユーザーの選択を返す (True/False) """
    dialog = ConfirmDialog(parent, title, message)
    return dialog.result


def show_error(title, message):
    """Show error """
    return messagebox.showerror(title, message)
