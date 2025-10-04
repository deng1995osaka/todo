import json
import time
import uuid
import requests
import threading
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, TASK_DECOMPOSITION_PROMPT, TASKS_PATH


@dataclass
class Task:
    """任务数据类（树形）"""
    id: str
    name: str
    completed: bool = False
    subtasks: List['Task'] = field(default_factory=list)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Task':
        return Task(
            id=data["id"],
            name=data["name"],
            completed=data.get("completed", False),
            subtasks=[Task.from_dict(t) for t in data.get("subtasks", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "completed": self.completed,
            "subtasks": [t.to_dict() for t in self.subtasks],
        }

class TaskManager:
    """任务管理器：内存 + JSON 持久化 + 分解API 调用"""
    def __init__(self):
        self.tasks: List[Task] = []
        self._lock = threading.Lock()
        self.load()  # 尝试从磁盘加载

    # ---------- 基础增删改查 ----------
    def _new_id(self) -> str:
        # 全局唯一，避免同父任务下重复
        return str(uuid.uuid4())

    def add_task(self, name: str, parent_id: Optional[str] = None) -> Task:
        with self._lock:
            task = Task(id=self._new_id(), name=name)
            if parent_id:
                parent = self.find_task(parent_id)
                if parent:
                    parent.subtasks.append(task)
                else:
                    # 父任务不存在则降级为顶层任务
                    self.tasks.append(task)
            else:
                self.tasks.append(task)
            self.save()
            return task

    def find_task(self, task_id: str) -> Optional[Task]:
        def dfs(tasks: List[Task]) -> Optional[Task]:
            for t in tasks:
                if t.id == task_id:
                    return t
                found = dfs(t.subtasks)
                if found:
                    return found
            return None
        return dfs(self.tasks)

    def toggle_task_completion(self, task_id: str) -> bool:
        with self._lock:
            task = self.find_task(task_id)
            if task:
                task.completed = not task.completed
                self.save()
                return True
            return False

    def get_all_tasks(self) -> List[Task]:
        return self.tasks

    def delete_task(self, task_id: str) -> bool:
        """删除任意层级任务，成功返回 True"""
        def _delete_in_list(lst):
            for i, t in enumerate(lst):
                if t.id == task_id:
                    lst.pop(i)
                    return True
                if _delete_in_list(t.subtasks):
                    return True
            return False

        with self._lock:
            ok = _delete_in_list(self.tasks)
            if ok:
                self.save()
            return ok

    # ---------- 持久化 ----------
    def load(self) -> None:
        try:
            with open(TASKS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        except FileNotFoundError:
            self.tasks = []
        except Exception:
            # 解析失败时安全降级：忽略旧文件
            self.tasks = []

    def save(self) -> None:
        data = {"tasks": [t.to_dict() for t in self.tasks]}
        with open(TASKS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- 任务分解（异步 + 重试 + 错误信息） ----------
    def decompose_task(self, task_id: str, callback=None) -> None:
        """调用DeepSeek将指定任务分解为子任务。callback签名：callback(success: bool, error: Optional[str])"""
        task = self.find_task(task_id)
        if not task:
            if callback:
                callback(False, "选中的任务不存在。")
            return

        def worker():
            # 快速失败：缺少API Key
            if not DEEPSEEK_API_KEY:
                if callback:
                    callback(False, "API Key 未设置（请配置环境变量 DEEPSEEK_API_KEY）。")
                return

            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            prompt = TASK_DECOMPOSITION_PROMPT.format(task_name=task.name)
            payload = {
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": "あなたは役立つアシスタントです。与えられたタスクをサブタスクのリストに分解し、必ず日本語で回答してください。回答は必ず数字で始まる箇条書きの形式で、余計な説明は不要です。"},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }

            last_error = None
            for attempt in range(3):  # 最多重试3次
                try:
                    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
                    resp.raise_for_status()
                    content = resp.json()["choices"][0]["message"]["content"]
                    subtasks = self._parse_subtasks(content)
                    with self._lock:
                        for name in subtasks:
                            if name:
                                task.subtasks.append(Task(id=self._new_id(), name=name))
                        self.save()
                    if callback:
                        callback(True, None)
                    return
                except requests.RequestException as e:
                    last_error = f"网络/请求错误：{e}"
                except (KeyError, ValueError) as e:
                    last_error = f"响应解析失败：{e}"
                # 指数退避
                time.sleep(2 ** attempt)

            if callback:
                callback(False, last_error or "未知错误")

        threading.Thread(target=worker, daemon=True).start()

    def _parse_subtasks(self, content: str) -> List[str]:
        # 尝试JSON，其次按"1. …"行解析
        try:
            data = json.loads(content)
            if isinstance(data, dict) and "subtasks" in data and isinstance(data["subtasks"], list):
                return [str(x).strip() for x in data["subtasks"] if str(x).strip()]
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
        except json.JSONDecodeError:
            pass

        lines = []
        for raw in content.splitlines():
            s = raw.strip()
            if not s:
                continue
            # 去掉前缀 "1. " / "1)" / "① " 等常见编号
            s = s.lstrip("・").replace(")", ".")
            import re
            s = re.sub(r"^[\d①-⑳]+\.\s*", "", s)
            if s and s[0] not in "{}[]":
                lines.append(s)
        return lines
