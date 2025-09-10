import tkinter as tk
import json
import requests
import threading
from typing import List, Dict, Optional
from dataclasses import dataclass
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, TASK_DECOMPOSITION_PROMPT

# 🍎 Apple Notes 风格的颜色和字体
class AppleNoteColors:
    BACKGROUND = "#fff8dc"  # 类纸张米黄色
    TEXT = "#3b3b3b"
    ENTRY_BG = "#fdf6e3"
    BUTTON_BG = "#f5f5f5"
    BUTTON_HOVER = "#e0e0e0"
    SELECT_BG = "#fff2b2"
    SELECT_TEXT = "#000000"

FONT_MAIN = ("Georgia", 13)

class AppleButton(tk.Button):
    """苹果 Notes 风格按钮"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            bg=AppleNoteColors.BUTTON_BG,
            fg=AppleNoteColors.TEXT,
            relief="flat",
            borderwidth=0,
            font=FONT_MAIN,
            activebackground=AppleNoteColors.BUTTON_HOVER,
            activeforeground=AppleNoteColors.TEXT,
            padx=10,
            pady=5
        )
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)

    def _on_hover(self, event):
        self.configure(bg=AppleNoteColors.BUTTON_HOVER, cursor="hand2")

    def _on_leave(self, event):
        self.configure(bg=AppleNoteColors.BUTTON_BG, cursor="")

class AppleEntry(tk.Entry):
    """苹果 Notes 风格输入框"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            bg=AppleNoteColors.ENTRY_BG,
            fg=AppleNoteColors.TEXT,
            relief="flat",
            font=FONT_MAIN,
            insertbackground=AppleNoteColors.TEXT,
            highlightthickness=1,
            highlightbackground="#ddd",
            highlightcolor="#aaa",
            bd=6
        )

class AppleCheckbutton(tk.Checkbutton):
    """苹果 Notes 风格复选框"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            bg=AppleNoteColors.BACKGROUND,
            fg=AppleNoteColors.TEXT,
            activebackground=AppleNoteColors.SELECT_BG,
            activeforeground=AppleNoteColors.SELECT_TEXT,
            selectcolor=AppleNoteColors.SELECT_BG,
            font=FONT_MAIN,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=6,
            pady=4,
            anchor="w"
        )

@dataclass
class Task:
    """任务数据类"""
    id: str
    name: str
    completed: bool = False
    subtasks: List['Task'] = None

    def __post_init__(self):
        if self.subtasks is None:
            self.subtasks = []

class TaskManager:
    """任务管理器类"""
    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, name: str, parent_id: Optional[str] = None) -> Task:
        """添加新任务"""
        task = Task(
            id=str(len(self.tasks) + 1),
            name=name
        )
        
        if parent_id:
            parent = self.find_task(parent_id)
            if parent:
                parent.subtasks.append(task)
        else:
            self.tasks.append(task)
        
        return task

    def find_task(self, task_id: str) -> Optional[Task]:
        """查找任务"""
        def search_in_tasks(tasks: List[Task]) -> Optional[Task]:
            for task in tasks:
                if task.id == task_id:
                    return task
                if task.subtasks:
                    result = search_in_tasks(task.subtasks)
                    if result:
                        return result
            return None
        
        return search_in_tasks(self.tasks)

    def toggle_task_completion(self, task_id: str) -> bool:
        """切换任务完成状态"""
        task = self.find_task(task_id)
        if task:
            task.completed = not task.completed
            return True
        return False

    def decompose_task(self, task_id: str, callback=None) -> None:
        """分解任务（异步）"""
        task = self.find_task(task_id)
        if not task:
            return

        def decompose_thread():
            try:
                # 准备API请求
                headers = {
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                # 准备提示词
                prompt = TASK_DECOMPOSITION_PROMPT.format(task_name=task.name)
                
                # 准备请求数据
                data = {
                    "model": DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": "あなたは役立つアシスタントです。与えられたタスクをサブタスクのリストに分解し、必ず日本語で回答してください。回答は必ず数字で始まる箇条書きの形式で、余計な説明は不要です。"},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                }
                
                # 发送API请求
                response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
                response.raise_for_status()
                
                # 解析响应
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                try:
                    # 尝试解析JSON格式
                    subtasks_data = json.loads(content)
                    if isinstance(subtasks_data, dict) and "subtasks" in subtasks_data:
                        subtasks = subtasks_data["subtasks"]
                    else:
                        # 如果不是预期的JSON格式，尝试直接解析文本
                        subtasks = self._clean_api_response(content)
                except json.JSONDecodeError:
                    # 如果JSON解析失败，使用文本解析
                    subtasks = self._clean_api_response(content)
                
                # 确保subtasks是列表
                if isinstance(subtasks, str):
                    subtasks = [task.strip() for task in subtasks.split('\n') if task.strip()]
                
                # 添加子任务
                for subtask_name in subtasks:
                    if subtask_name:  # 确保子任务名称不为空
                        self.add_task(subtask_name, task_id)
                
                if callback:
                    callback(True)
            except Exception as e:
                if callback:
                    callback(False)

        thread = threading.Thread(target=decompose_thread)
        thread.start()

    def _clean_api_response(self, content: str) -> List[str]:
        """清理API响应内容，返回子任务列表"""
        import re
        # 提取数字编号开头的行
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # 移除数字编号和多余的空格
            cleaned_line = re.sub(r'^\d+\.\s*', '', line.strip())
            if cleaned_line and not cleaned_line.startswith('{') and not cleaned_line.startswith('}'):
                cleaned_lines.append(cleaned_line)
        return cleaned_lines

    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self.tasks

class TodoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("タスク管理")
        self.root.geometry("400x600")
        self.root.configure(bg=AppleNoteColors.BACKGROUND)
        self.root.overrideredirect(False)
        
        self.task_manager = TaskManager()
        self.selected_task = None  # 添加选中任务的属性
        self._create_widgets()
        self._setup_layout()
        
        # 初始化任务列表
        self.check_vars = []
        self.task_widgets = []
        for idx, task in enumerate(self.task_manager.get_all_tasks()):
            self._add_task_checkbutton(task, idx)

    def _create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        self.main_frame = tk.Frame(self.root, bg=AppleNoteColors.BACKGROUND)
        
        # 创建输入区域
        self.input_frame = tk.Frame(self.main_frame, bg=AppleNoteColors.BACKGROUND)
        self.task_entry = AppleEntry(self.input_frame)
        self.add_button = AppleButton(self.input_frame, text="タスク追加", command=self._add_task)
        
        # 创建任务列表区域（用Frame代替Listbox）
        self.list_frame = tk.Frame(self.main_frame, bg=AppleNoteColors.BACKGROUND)
        self.tasks_container = tk.Frame(self.list_frame, bg=AppleNoteColors.BACKGROUND)
        self.tasks_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建按钮区域（只保留Decompose按钮）
        self.button_frame = tk.Frame(self.main_frame, bg=AppleNoteColors.BACKGROUND)
        self.decompose_button = AppleButton(self.button_frame, text="分解", command=self._decompose_task)

    def _setup_layout(self):
        """设置界面布局"""
        # 主容器
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 10))
        
        # 输入区域
        self.input_frame.pack(fill=tk.X, pady=(0, 10))
        self.task_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.add_button.pack(side=tk.RIGHT)
        
        # 任务列表区域
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        self.tasks_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 按钮区域
        self.button_frame.pack(fill=tk.X, pady=(10, 0))
        self.decompose_button.pack(side=tk.LEFT, padx=5)

    def _add_task_checkbutton(self, task, idx, level=0):
        if level == 0:  # 主任务使用复选框
            var = tk.BooleanVar(value=task.completed)
            cb = AppleCheckbutton(
                self.tasks_container,
                text=task.name,
                variable=var,
                command=lambda t=task, v=var: self._toggle_task_completion(t, v)
            )
            # 添加点击事件来选择任务
            cb.bind("<Button-1>", lambda e, t=task: self._select_task(t))
            cb.pack(anchor="w", padx=10, pady=2, fill=tk.X)
            self.check_vars.append(var)
            self.task_widgets.append(cb)
        else:  # 子任务使用标签
            label = tk.Label(
                self.tasks_container,
                text=("  " * level) + "• " + task.name,
                bg=AppleNoteColors.BACKGROUND,
                fg=AppleNoteColors.TEXT,
                font=FONT_MAIN,
                anchor="w"
            )
            label.pack(anchor="w", padx=10+level*20, pady=2, fill=tk.X)
            self.task_widgets.append(label)
        
        for subtask in task.subtasks:
            self._add_task_checkbutton(subtask, idx, level+1)

    def _select_task(self, task):
        """选择任务"""
        self.selected_task = task
        # 更新所有复选框的样式
        for widget in self.task_widgets:
            if isinstance(widget, AppleCheckbutton):
                if widget.cget("text") == task.name:
                    widget.configure(bg=AppleNoteColors.SELECT_BG)
                else:
                    widget.configure(bg=AppleNoteColors.BACKGROUND)

    def _add_task(self):
        """添加新任务"""
        task_name = self.task_entry.get().strip()
        if task_name:
            task = self.task_manager.add_task(task_name)
            self.task_entry.delete(0, tk.END)
            # 清除现有任务列表
            for widget in self.tasks_container.winfo_children():
                widget.destroy()
            self.check_vars = []
            self.task_widgets = []
            # 重新添加所有任务
            for idx, task in enumerate(self.task_manager.get_all_tasks()):
                self._add_task_checkbutton(task, idx)

    def _toggle_task_completion(self, task, var):
        self.task_manager.toggle_task_completion(task.id)
        # 清除现有任务列表
        for widget in self.tasks_container.winfo_children():
            widget.destroy()
        self.check_vars = []
        self.task_widgets = []
        # 重新添加所有任务
        for idx, task in enumerate(self.task_manager.get_all_tasks()):
            self._add_task_checkbutton(task, idx)

    def _decompose_task(self):
        """分解选中的任务"""
        if not self.selected_task:
            return
        
        def on_decompose_complete(success):
            if success:
                # 清除现有任务列表
                for widget in self.tasks_container.winfo_children():
                    widget.destroy()
                self.check_vars = []
                self.task_widgets = []
                # 重新添加所有任务
                for idx, task in enumerate(self.task_manager.get_all_tasks()):
                    self._add_task_checkbutton(task, idx)
        
        self.task_manager.decompose_task(self.selected_task.id, on_decompose_complete)

    def run(self):
        """运行应用程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TodoApp()
    app.run()
