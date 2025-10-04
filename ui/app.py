"""Main application class for the Todo application"""
import tkinter as tk
from tkinter import ttk



# Import our modular components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.task_manager import TaskManager, Task
from ui.components import AppleButton, AppleEntry, AppleRadiobutton, show_confirm, show_error
from style.theme import Theme


class TodoApp:
    """Main application class for the Todo application"""
    
    def __init__(self, root):
        self.root = root
        self.task_manager = TaskManager()
        self.selected_task_id: str | None = None  # 单选状态
        self.marked_ids: set[str] = set()   # 存放"被划线"的任务ID，可叠加
        self.expanded_ids: set[str] = set()  # 记录"已展开"的任务ID

        # 初始化字体（普通 / 删除线）
        self.font_normal = Theme.Font.get()
        self.font_overstrike = Theme.Font.get(overstrike=True)

        self._setup_window()
        self._build_ui()
        
        # 顶层默认展开（在第一次刷新前设置，或者设置后再刷新一次）
        for t in self.task_manager.get_all_tasks():
            self.expanded_ids.add(t.id)
        
        self._refresh_ui()

    def _setup_window(self):
        """Configure the main window"""
        self.root.title("タスク管理")
        self.root.geometry("420x640")
        self.root.configure(bg=Theme.Color.BACKGROUND)

    def _build_ui(self):
        """Build the user interface"""
        self.main_frame = tk.Frame(self.root, bg=Theme.Color.BACKGROUND)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 10))

        # 顶部输入行
        self.input_frame = tk.Frame(self.main_frame, bg=Theme.Color.BACKGROUND)
        self.input_frame.pack(fill=tk.X, pady=(0, 10))
        self.task_entry = AppleEntry(self.input_frame)
        self.task_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.add_button = AppleButton(self.input_frame, text="タスク追加", command=self._add_task)
        self.add_button.pack(side=tk.RIGHT)

        # 任务列表
        self.list_frame = tk.Frame(self.main_frame, bg=Theme.Color.BACKGROUND)
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        # 滚动区域
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

        # 底部按钮区域
        self.bottom_frame = tk.Frame(self.main_frame, bg=Theme.Color.BACKGROUND)
        self.bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 分解按钮
        self.decompose_button = AppleButton(self.bottom_frame, text="分解", command=self._decompose_task)
        self.decompose_button.pack(side=tk.LEFT, padx=5)
        
        # 删除按钮
        self.delete_button = AppleButton(self.bottom_frame, text="削除", command=self._delete_selected)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # 进度条区域
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
        
        # 进度条样式优化
        self.style = ttk.Style()
        self.style.configure("Thick.Horizontal.TProgressbar", 
                           troughcolor=Theme.Color.PROGRESS_BAR_TROUGH, 
                           thickness=10)
        self.progressbar.configure(style="Thick.Horizontal.TProgressbar")

    def _refresh_ui(self):
        """Refresh the UI to reflect current state"""
        # 清空容器
        for w in self.tasks_container.winfo_children():
            w.destroy()

        self._radio_vars = []  # 改为存储Radio button变量
        self._task_widgets = []

        for task in self.task_manager.get_all_tasks():
            self._add_task_widget(task, level=0)
        
        # 更新底部按钮状态
        self._update_bottom_buttons()
        # 刷新进度条
        self._refresh_progress()

    def _add_task_widget(self, task: Task, level: int):
        """Add a task widget to the UI"""
        # 行容器
        row = tk.Frame(self.tasks_container, bg=Theme.Color.BACKGROUND)
        row.pack(anchor="w", fill=tk.X, pady=2)

        has_children = bool(task.subtasks)

        # 右侧"展开/收起"三角（有子项才显示）
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
            # 母项目：使用Radio button
            var = tk.BooleanVar(value=(self.selected_task_id == task.id))
            rb = AppleRadiobutton(
                row,
                text=task.name,
                variable=var,
                value=True,
                command=lambda t=task: self._select_parent_task(t)
            )
            # auto-wrap for radio buttons
            try:
                wrap_px = max(160, 340 - level*20)
                rb.configure(wraplength=wrap_px, justify='left')
            except Exception:
                pass
            rb.grid(row=0, column=0, padx=10 + level*20, pady=2, sticky="ew")
            
            # 母项目不能划线，统一背景色
            rb.configure(
                bg=Theme.Color.BACKGROUND,
                font=self.font_normal
            )

            self._radio_vars.append(var)
            self._task_widgets.append(rb)
        else:
            # 子项目：只显示文本，可以划线
            is_marked = (task.id in self.marked_ids)
            label = tk.Label(
                row,
                text=task.name,
                bg=Theme.Color.BACKGROUND,
                fg=Theme.Color.TEXT,
                font=self.font_overstrike if is_marked else self.font_normal,
                anchor="w"
            )
            # auto-wrap for labels
            try:
                wrap_px = max(160, 340 - level*20)
                label.configure(wraplength=wrap_px, justify='left')
            except Exception:
                pass
            label.grid(row=0, column=0, padx=10 + level*20, pady=2, sticky="ew")
            
            # 子项目可以点击划线
            label.bind("<Button-1>", lambda e, t=task: self._toggle_mark_subtask(t))
            label.bind("<Enter>",  lambda e: label.config(cursor="hand2"))
            label.bind("<Leave>",  lambda e: label.config(cursor=""))

            self._task_widgets.append(label)

        # 递归渲染子项：仅当"已展开"时才渲染
        if has_children and (task.id in self.expanded_ids):
            for sub in task.subtasks:
                self._add_task_widget(sub, level+1)

    def _toggle_expand(self, task: Task):
        """切换展开/收起状态 - 手风琴效果，同时只能有一个母项目展开"""
        if task.id in self.expanded_ids:
            # 如果当前任务已展开，则收起
            self.expanded_ids.remove(task.id)
        else:
            # 如果当前任务未展开，则先清空所有展开状态，再展开当前任务
            self.expanded_ids.clear()
            self.expanded_ids.add(task.id)
        self._refresh_ui()

    def _select_parent_task(self, task: Task):
        """选择母项目（通过Radio button）- 手风琴效果：选择新项目时自动收起其他展开的项目"""
        self.selected_task_id = task.id
        
        # 🎯 手风琴效果：选择新项目时，收起其他所有展开的项目
        self.expanded_ids.clear()
        
        self._refresh_ui()

    def _toggle_mark_subtask(self, task: Task):
        """切换子项目的标记状态（划线）"""
        if task.id in self.marked_ids:
            self.marked_ids.remove(task.id)
        else:
            self.marked_ids.add(task.id)
        self._refresh_ui()

    def _iter_descendants(self, task: Task):
        """遍历 task 的全部子孙（不含父本身）"""
        for st in task.subtasks:
            yield st
            yield from self._iter_descendants(st)

    def _marked_progress_for(self, task: Task) -> tuple[int, int]:
        """返回 (已标记数量, 子项目总数)，不含父本身"""
        nodes = list(self._iter_descendants(task))
        total = len(nodes)
        marked = sum(1 for n in nodes if n.id in self.marked_ids)
        return marked, total

    def _get_selected_task(self) -> Task | None:
        """获取当前选中的任务对象"""
        if not self.selected_task_id:
            return None
        return self.task_manager.find_task(self.selected_task_id)

    def _refresh_progress(self):
        """刷新底部进度条 - 显示已展开任务的进度（不管是否选中）"""
        # 获取已展开的任务（手风琴效果，同时只有一个）
        expanded_task = None
        for task in self.task_manager.get_all_tasks():
            if task.id in self.expanded_ids:
                expanded_task = task
                break
        
        if not expanded_task or not expanded_task.subtasks:
            # 没有已展开的任务或已展开的任务没有子项，隐藏进度条
            self.progress_frame.pack_forget()
            return
        
        # 显示进度条：有已展开的任务
        self.progress_frame.pack(side=tk.LEFT, padx=5)
        
        marked, total = self._marked_progress_for(expanded_task)  # 根据"标记集合"统计
        percent = int(marked * 100 / total) if total else 0
        self.progressbar["value"] = percent
        self.progress_label.configure(text=f"{percent}%")

    def _update_bottom_buttons(self):
        """根据是否选中任务启用/禁用底部按钮"""
        has_sel = self.selected_task_id is not None
        if not has_sel:
            # 没有选中任务，两个按钮都禁用
            self.decompose_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            return
        
        # 有选中任务，检查分解按钮的启用条件
        task = self._get_selected_task()
        if task and not task.subtasks:
            # 有选中 & 没有子项 → 分解按钮可点
            self.decompose_button.configure(state="normal")
        else:
            # 其他情况 → 分解按钮禁用
            self.decompose_button.configure(state="disabled")
        
        # 删除按钮始终可用（有选中任务时）
        self.delete_button.configure(state="normal")

    def _set_busy(self, busy: bool, msg: str = ""):
        """忙碌状态管理"""
        if busy:
            # 保存原始按钮文本，如果还没有保存的话
            if not hasattr(self, '_original_decompose_text'):
                self._original_decompose_text = self.decompose_button.cget("text")
            
            # 更新按钮文本为忙碌状态
            if msg:
                self.decompose_button.configure(text=msg)
            
            self.decompose_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
        else:
            # 恢复原始按钮文本
            if hasattr(self, '_original_decompose_text'):
                self.decompose_button.configure(text=self._original_decompose_text)
            
            # 非忙碌状态下，重新计算按钮状态
            self._update_bottom_buttons()
        
        self.add_button.configure(state=("disabled" if busy else "normal"))
        self.root.configure(cursor="watch" if busy else "")

    def _add_task(self):
        """Add a new task"""
        name = self.task_entry.get().strip()
        if not name:
            return
        self.task_manager.add_task(name)
        self.task_entry.delete(0, tk.END)
        self._refresh_ui()

    def _decompose_task(self):
        """Decompose the selected task"""
        if not self.selected_task_id:
            return
        self._set_busy(True, "分解中…")

        def on_complete(success: bool, error: str | None):
            # 回到主线程刷新
            self.root.after(0, lambda: self._on_decompose_done(success, error))

        self.task_manager.decompose_task(self.selected_task_id, on_complete)

    def _on_decompose_done(self, success: bool, error: str | None):
        """Handle decomposition completion"""
        self._set_busy(False, "")
        if success:
            # 分解完成后自动展开该任务
            if self.selected_task_id:
                self.expanded_ids.clear()  # 手风琴效果：先清空其他展开
                self.expanded_ids.add(self.selected_task_id)  # 展开当前任务
            self._refresh_ui()
        else:
            message = error or "未知错误"
            show_error("分解失败", message)

    def _delete_selected(self):
        """删除当前选中的任务 - 使用自定义确认对话框"""
        if not self.selected_task_id:
            return
        
        # 🎯 使用自定义确认对话框替换系统弹窗，在"しますか？"后面换行
        if not show_confirm(self.root, "確認", "選択中のタスクを削除しますか？\n（サブタスクごと削除）"):
            return
        
        ok = self.task_manager.delete_task(self.selected_task_id)
        if not ok:
            show_error("エラー", "削除に失敗しました。")
            return
        # 清空选中并刷新
        self.selected_task_id = None
        self._refresh_ui()

    def run(self):
        """Start the application main loop"""
        self.root.mainloop()


def run_app():
    """Application entry point function"""
    root = tk.Tk()
    app = TodoApp(root)
    app.run()


if __name__ == "__main__":
    """Todo Application Entry Point
    
    This is the main entry point for the Todo application.
    The application has been refactored into a modular structure:
    
    - ui/app.py: Main application class and UI logic
    - ui/components.py: Custom UI components and dialogs
    - logic/: Business logic and data management
    - style/: Theme and styling configuration
    """
    run_app()