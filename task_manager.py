import json
import requests
import threading
from typing import List, Dict, Optional
from dataclasses import dataclass
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, TASK_DECOMPOSITION_PROMPT

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
