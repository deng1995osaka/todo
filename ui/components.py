"""UI Components for the Todo application with Apple Notes styling"""
import tkinter as tk
from tkinter import messagebox
from style.theme import Theme


# ============================================================================
# Custom Widgets
# ============================================================================

class AppleButton(tk.Button):
    """Custom button with Apple Notes styling and hover effects"""
    
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
        """Handle mouse hover effect"""
        self.configure(bg=Theme.Color.BUTTON_HOVER, cursor="hand2")

    def _on_leave(self, event):
        """Handle mouse leave effect"""
        self.configure(bg=Theme.Color.BUTTON_BG, cursor="")


class AppleEntry(tk.Entry):
    """Custom entry field with Apple Notes styling"""
    
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
    """Custom radio button with Apple Notes styling"""
    
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
# Custom Dialogs
# ============================================================================

class ConfirmDialog(tk.Toplevel):
    """简洁的确认对话框，在父窗口居中显示"""

    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.result = False

        # 窗口设置
        self.title(title)
        self.configure(bg=Theme.Color.BACKGROUND)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # 创建UI
        main_frame = tk.Frame(self, bg=Theme.Color.BACKGROUND, padx=30, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # 消息标签
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

        # 按钮
        button_frame = tk.Frame(main_frame, bg=Theme.Color.BACKGROUND)
        button_frame.pack()

        self.confirm_button = AppleButton(button_frame, text="确定", width=8, command=self._on_confirm)
        self.confirm_button.pack(side=tk.LEFT, padx=10)

        self.cancel_button = AppleButton(button_frame, text="キャンセル", width=8, command=self._on_cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=10)

        # 键盘绑定
        self.bind('<Return>', lambda e: self._on_confirm())
        self.bind('<Escape>', lambda e: self._on_cancel())

        # 居中显示
        self._center_on_parent()
        self.wait_window(self)

    def _center_on_parent(self):
        """将对话框居中于父窗口"""
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
# Convenience Functions
# ============================================================================

def show_confirm(parent, title="确认", message="确定要执行此操作吗？"):
    """显示确认对话框，返回用户选择 (True/False)"""
    dialog = ConfirmDialog(parent, title, message)
    return dialog.result


def show_error(title, message):
    """显示错误对话框"""
    return messagebox.showerror(title, message)
