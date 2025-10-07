
import tkinter as tk
from tkinter import ttk



import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.task_manager import TaskManager, Task
from ui.components import AppleButton, AppleEntry, AppleRadiobutton, show_confirm, show_error
from style.theme import Theme

# ==================== Application Class ====================


class TodoApp:
    """ Main application class for the Todo application"""
    
    def __init__(self, root):
        self.root = root
        self.task_manager = TaskManager()
        self.selected_task_id: str | None = None  # 選択状態 
        self.expanded_ids: set[str] = set()  # "展開済み"のタスクIDを記録 

        # フォントを初期化（通常 / 取り消し線）
        self.font_normal = Theme.Font.get()
        self.font_overstrike = Theme.Font.get(overstrike=True)

        self._setup_window()
        self._build_ui()
        
        # Top levelをdefaultで展開
        for t in self.task_manager.get_all_tasks():
            self.expanded_ids.add(t.id)
        
        self._refresh_ui()

    def _setup_window(self):
        """main windowを設定 """
        self.root.title("タスク管理")
        self.root.geometry("420x640")
        self.root.configure(bg=Theme.Color.BACKGROUND)

    def _build_ui(self):
        """ Build the user interface"""
        self.main_frame = tk.Frame(self.root, bg=Theme.Color.BACKGROUND)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 10))

        # -------------------- 入力エリア --------------------
      
        self.input_frame = tk.Frame(self.main_frame, bg=Theme.Color.BACKGROUND)
        self.input_frame.pack(fill=tk.X, pady=(0, 10))
        self.task_entry = AppleEntry(self.input_frame)
        self.task_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.add_button = AppleButton(self.input_frame, text="タスク追加", command=self._add_task)
        self.add_button.pack(side=tk.RIGHT)

        # -------------------- Task List --------------------
       
        self.list_frame = tk.Frame(self.main_frame, bg=Theme.Color.BACKGROUND)
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        #  Scroll area
        self.canvas = tk.Canvas(self.list_frame, bg=Theme.Color.BACKGROUND, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.list_frame, orient="vertical", command=self.canvas.yview)
        self.tasks_container = tk.Frame(self.canvas, bg=Theme.Color.BACKGROUND)
        self.tasks_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.tasks_container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # -------------------- Buttons --------------------
      
        self.bottom_frame = tk.Frame(self.main_frame, bg=Theme.Color.BACKGROUND)
        self.bottom_frame.pack(fill=tk.X, pady=(10, 0))
     
        
        # 分解ボタン 
        self.decompose_button = AppleButton(self.bottom_frame, text="分解", command=self._decompose_task)
        self.decompose_button.pack(side=tk.LEFT, padx=5)
        
        # 削除ボタン 
        self.delete_button = AppleButton(self.bottom_frame, text="削除", command=self._delete_selected)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # -------------------- Progress Bar --------------------
       
        self.progress_frame = tk.Frame(self.bottom_frame, bg=Theme.Color.BACKGROUND)
        self.progress_frame.pack(side=tk.LEFT, padx=5)

        self.progress_label = tk.Label(
            self.progress_frame,
            text="0%",
            bg=Theme.Color.BACKGROUND,
            fg=Theme.Color.FADED_TEXT,
            font=("Arial", 11)
        )
        self.progress_label.pack(side=tk.RIGHT, padx=(6, 0))

        self.progressbar = ttk.Progressbar(
            self.progress_frame,
            orient="horizontal",
            mode="determinate",
            length=140
        )
        self.progressbar.pack(side=tk.LEFT)
        
        # Progress bar style optimization
        self.style = ttk.Style()
        self.style.configure("Thick.Horizontal.TProgressbar", 
                           troughcolor=Theme.Color.PROGRESS_BAR_TROUGH, 
                           thickness=10)
        self.progressbar.configure(style="Thick.Horizontal.TProgressbar")

    # ==================== UI Refresh & Rendering ====================
    def _refresh_ui(self):
        
        # Clear container
        for w in self.tasks_container.winfo_children():
            w.destroy()

        self._radio_vars = []  # Changed to store Radio button variables
        self._task_widgets = []

        for task in self.task_manager.get_all_tasks():
            self._add_task_widget(task, level=0)
        
        # bottom_buttons状態を更新 
        self._update_bottom_buttons()
        # Refresh progress bar
        self._refresh_progress()

    # -------------------- Task行の描画 --------------------
    def _add_task_widget(self, task: Task, level: int):
        """UIにtask widgetを追加 """
        # Row container
        row = tk.Frame(self.tasks_container, bg=Theme.Color.BACKGROUND)
        row.pack(anchor="w", fill=tk.X, pady=2)

        has_children = bool(task.subtasks)

        # 右側"展開/収納"三角
        if has_children:
            is_open = (task.id in self.expanded_ids)
            glyph = "▾" if is_open else "▸"
            toggle = tk.Label(
                row,
                text=glyph,
                bg=Theme.Color.BACKGROUND,
                fg=Theme.Color.TEXT,
                font=Theme.Font.get(),
                width=2
            )
            toggle.grid(row=0, column=2, padx=(4, 8), sticky="e")
            toggle.bind("<Button-1>", lambda e, t=task: self._toggle_expand(t))
            toggle.bind("<Enter>",  lambda e: toggle.config(cursor="hand2"))
            toggle.bind("<Leave>",  lambda e: toggle.config(cursor=""))

        if level == 0:
            # Radio buttonを使用 
            var = tk.BooleanVar(value=(self.selected_task_id == task.id))
            rb = AppleRadiobutton(
                row,
                text=task.name,
                variable=var,
                value=True,
                command=lambda t=task: self._select_parent_task(t)
            )
            # radio buttonのauto-wrap 
            try:
                wrap_px = max(160, 340 - level*20)
                rb.configure(wraplength=wrap_px, justify='left')
            except Exception:
                pass
            rb.grid(row=0, column=0, padx=10 + level*20, pady=2, sticky="ew")
            
            # 親項目：線引き不可
            rb.configure(
                bg=Theme.Color.BACKGROUND,
                font=self.font_normal
            )

            self._radio_vars.append(var)
            self._task_widgets.append(rb)
        else:
            # 子項目：テキストのみ表示、線引き可能 
            is_marked = task.completed
            label = tk.Label(
                row,
                text=task.name,
                bg=Theme.Color.BACKGROUND,
                fg=Theme.Color.TEXT,
                font=self.font_overstrike if is_marked else self.font_normal,
                anchor="w"
            )
            # 子項目のauto-wrap 
            try:
                wrap_px = max(160, 340 - level*20)
                label.configure(wraplength=wrap_px, justify='left')
            except Exception:
                pass
            label.grid(row=0, column=0, padx=10 + level*20, pady=2, sticky="ew")
            
            # 子項目はクリックで線引き可能 
            label.bind("<Button-1>", lambda e, t=task: self._toggle_mark_subtask(t))
            label.bind("<Enter>",  lambda e: label.config(cursor="hand2"))
            label.bind("<Leave>",  lambda e: label.config(cursor=""))

            self._task_widgets.append(label)

        # 子項目を再帰的にレンダリング：「展開済み」の場合のみ 
        if has_children and (task.id in self.expanded_ids):
            for sub in task.subtasks:
                self._add_task_widget(sub, level+1)

    # ==================== Event Handlers ====================
    def _toggle_expand(self, task: Task):
        """展開/収納状態を切り替え - 同時に1つの親項目のみ展開可能 """
        if task.id in self.expanded_ids:
            # 現在のタスクが展開済みの場合、収納 
            self.expanded_ids.remove(task.id)
        else:
            # 現在のタスクが未展開の場合、すべての展開状態をクリアしてから現在のタスクを展開 
            self.expanded_ids.clear()
            self.expanded_ids.add(task.id)
        self._refresh_ui()

    def _select_parent_task(self, task: Task):
        """新しい項目を選択時に他の展開項目を自動収納 """
        self.selected_task_id = task.id
        
        self.expanded_ids.clear()
        
        self._refresh_ui()

    def _toggle_mark_subtask(self, task: Task):
        """子項目の線引きを切り替え"""
        
        self.task_manager.toggle_task_completion(task.id)
        self._refresh_ui()

    # ==================== Utilities ====================
    def _iter_descendants(self, task: Task):
        """タスクのすべての子孫を走査（親自体は含まない）"""
        for st in task.subtasks:
            yield st
            yield from self._iter_descendants(st)

    def _marked_progress_for(self, task: Task) -> tuple[int, int]:
        """（マーク済み数、子項目総数）を返す、親自体は含まない """
        nodes = list(self._iter_descendants(task))
        total = len(nodes)
        marked = sum(1 for n in nodes if n.completed)
        return marked, total

    def _get_selected_task(self) -> Task | None:
        """現在選択されているtask objectを取得 """
        if not self.selected_task_id:
            return None
        return self.task_manager.find_task(self.selected_task_id)

    # ==================== Progress Update ====================
    def _refresh_progress(self):
        """Progress barをリフレッシュ """
        # 展開済みタスクを取得
        expanded_task = None
        for task in self.task_manager.get_all_tasks():
            if task.id in self.expanded_ids:
                expanded_task = task
                break
        
        if not expanded_task or not expanded_task.subtasks:
            # 展開済みタスクがない、または展開済みタスクに子項目がない場合、progress barを非表示 
            self.progress_frame.pack_forget()
            return
        
        # progress barを表示：展開済みタスクがある場合 
        self.progress_frame.pack(side=tk.LEFT, padx=5)
        
        marked, total = self._marked_progress_for(expanded_task)  # "マーク集合"に基づいて統計 
        percent = int(marked * 100 / total) if total else 0
        self.progressbar["value"] = percent
        self.progress_label.configure(text=f"{percent}%")

    # ==================== Buttons状態更新 ====================
    def _update_bottom_buttons(self):
        """taskの選択状態に基づいてbottom buttonsを有効/無効化 """
        has_sel = self.selected_task_id is not None
        if not has_sel:
            # 選択されたtaskがない場合、両方のボタンを無効化 
            self.decompose_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            return
        
        # 選択されたtaskがある場合、分解ボタンの有効化条件をチェック 
        task = self._get_selected_task()
        if task and not task.subtasks:
            # 選択済み & 子項目なし → 分解ボタンクリック可能 
            self.decompose_button.configure(state="normal")
        else:
            # その他の場合 → 分解ボタン無効 
            self.decompose_button.configure(state="disabled")
        
        # 削除ボタンは常に利用可能（選択されたtaskがある場合）
        self.delete_button.configure(state="normal")

    # ==================== Busy状態管理 ====================
    def _set_busy(self, busy: bool, msg: str = ""):
        
        if busy:
            # 元のボタンテキストを保存、まだ保存されていない場合 
            if not hasattr(self, '_original_decompose_text'):
                self._original_decompose_text = self.decompose_button.cget("text")
            
            # ボタンテキストをbusy状態に更新 
            if msg:
                self.decompose_button.configure(text=msg)
            
            self.decompose_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
        else:
            # 元のボタンテキストを復元 
            if hasattr(self, '_original_decompose_text'):
                self.decompose_button.configure(text=self._original_decompose_text)
            
            # 非busy状態で、ボタン状態を再計算 
            self._update_bottom_buttons()
        
        self.add_button.configure(state=("disabled" if busy else "normal"))
        self.root.configure(cursor="watch" if busy else "")

    # ==================== Task操作 ====================
    def _add_task(self):
        """新しいタスクを追加 """
        name = self.task_entry.get().strip()
        if not name:
            return
        self.task_manager.add_task(name)
        self.task_entry.delete(0, tk.END)
        self._refresh_ui()

    def _decompose_task(self):
        """選択されたタスクを分解 """
        if not self.selected_task_id:
            return
        self._set_busy(True, "分解中…")

        def on_complete(success: bool, error: str | None):
            #  Return to main thread and refresh
            self.root.after(0, lambda: self._on_decompose_done(success, error))

        self.task_manager.decompose_task(self.selected_task_id, on_complete)

    def _on_decompose_done(self, success: bool, error: str | None):
        """分解完了処理 """
        self._set_busy(False, "")
        if success:
            # 分解完了後に自動的にそのタスクを展開 
            if self.selected_task_id:
                self.expanded_ids.clear()  # まず他の展開をクリア 
                self.expanded_ids.add(self.selected_task_id)  # 現在のタスクを展開 
            self._refresh_ui()
        else:
            message = error or "未知のエラー"  # Unknown error
            show_error("分解失敗", message)

    def _delete_selected(self):
        """現在選択されているタスクを削除 """
        if not self.selected_task_id:
            return
        
        
        if not show_confirm(self.root, "確認", "選択中のタスクを削除しますか？\n（サブタスクごと削除）"):
            return
        
        ok = self.task_manager.delete_task(self.selected_task_id)
        if not ok:
            show_error("エラー", "削除に失敗しました。")
            return
        # 選択をクリアしてリrefresh 
        self.selected_task_id = None
        self._refresh_ui()

    # ==================== アプリケーション起動 ====================
    def run(self):
        """ Start the application main loop"""
        self.root.mainloop()


# ==================== Entry Points ====================
def run_app():
   
    root = tk.Tk()
    app = TodoApp(root)
    app.run()


if __name__ == "__main__":
    """ Todo Application Entry Point
    
    This is the main entry point for the Todo application.
    The application has been refactored into a modular structure:
    
    - ui/app.py: Main application class and UI logic
    - ui/components.py: Custom UI components and dialogs
    - logic/: Business logic and data management
    - style/: Theme and styling configuration
    """
    run_app()