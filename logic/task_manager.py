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
    """Task data class（ツリー構造）"""
    id: str
    name: str
    completed: bool = False
    subtasks: List['Task'] = field(default_factory=list)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Task':
        """辞書からタスクを作成 """
        return Task(
            id=data["id"],
            name=data["name"],
            completed=data.get("completed", False),
            subtasks=[Task.from_dict(t) for t in data.get("subtasks", [])],
        )

    def to_dict(self) -> Dict[str, Any]:
        """タスクを辞書に変換 """
        return {
            "id": self.id,
            "name": self.name,
            "completed": self.completed,
            "subtasks": [t.to_dict() for t in self.subtasks],
        }

class TaskManager:
    """Task manager：メモリ + JSON保存 + 分解API呼び出し """
    def __init__(self):
        self.tasks: List[Task] = []
        self._lock = threading.Lock()  # thread安全のためのロック 
        self.load()  # diskから読み込みを試行 

    # ---------- 基本のCRUD操作  ----------
    def _new_id(self) -> str:
        """globally uniqueなIDを生成 """
        return str(uuid.uuid4())

    def add_task(self, name: str) -> Task:
        """新しいタスクを追加 """
        with self._lock:
            task = Task(id=self._new_id(), name=name)
            # 常にトップレベルに追加
            self.tasks.append(task)
            self.save()
            return task

    def find_task(self, task_id: str) -> Optional[Task]:
        """指定されたIDのタスクを検索 / Find task by ID"""
        def dfs(tasks: List[Task]) -> Optional[Task]:
            """深さ優先探索 / Depth-first search"""
            for t in tasks:
                if t.id == task_id:
                    return t
                found = dfs(t.subtasks)
                if found:
                    return found
            return None
        return dfs(self.tasks)

    def toggle_task_completion(self, task_id: str) -> bool:
        """タスクの完了状態を切り替え / Toggle task completion status"""
        with self._lock:
            task = self.find_task(task_id)
            if task:
                task.completed = not task.completed
                self.save()
                return True
            return False

    def get_all_tasks(self) -> List[Task]:
        """すべてのタスクを取得 """
        return self.tasks

    def delete_task(self, task_id: str) -> bool:
        """トップレベル（母プロジェクト）のみ削除。子タスクは削除不可。成功時Trueを返す"""
        with self._lock:
            for i, t in enumerate(self.tasks):
                if t.id == task_id:
                    self.tasks.pop(i)
                    self.save()
                    return True
            return False

    # ---------- データの永続化  ----------
    def load(self) -> None:
        """JSONファイルからタスクを読み込み / Load tasks from JSON file"""
        try:
            with open(TASKS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        except FileNotFoundError:
            self.tasks = []  # ファイルが存在しない場合は空のリスト 
        except Exception:
            # 解析失敗時は安全に降格：古いファイルを無視 
            self.tasks = []

    def save(self) -> None:
        """タスクをJSONファイルに保存 / Save tasks to JSON file"""
        data = {"tasks": [t.to_dict() for t in self.tasks]}
        with open(TASKS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- タスク分解（非同期 + retry + エラー情報） ----------
    def decompose_task(self, task_id: str, callback=None) -> None:
        """DeepSeekを呼び出して指定されたタスクをサブタスクに分解 """
        task = self.find_task(task_id)
        if not task:
            if callback:
                callback(False, "選択されたタスクが存在しません。")  # Selected task doesn't exist
            return

        def worker():
            """ Background worker 関数"""
            # Quick fail：API Keyが不足 
            if not DEEPSEEK_API_KEY:
                if callback:
                    callback(False, "API Keyが設定されていません（環境変数DEEPSEEK_API_KEYを設定してください）。")
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
            for attempt in range(3):  # 最大3回retries 
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
                    last_error = f"ネットワーク/リクエストエラー：{e}"  # Network/request error
                except (KeyError, ValueError) as e:
                    last_error = f"レスポンス解析失敗：{e}"  
                # 指数backoff 
                time.sleep(2 ** attempt)

            if callback:
                callback(False, last_error or "未知のエラー")  

        threading.Thread(target=worker, daemon=True).start()

    def _parse_subtasks(self, content: str) -> List[str]:
        """サブタスクを解析 / Parse subtasks"""
        # まずJSONを試し、次に"1. …"行で解析 
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
            # プレフィックス "1. " / "1)" / "① " などの一般的な番号を削除 
            s = s.lstrip("・").replace(")", ".")
            import re
            s = re.sub(r"^[\d①-⑳]+\.\s*", "", s)
            if s and s[0] not in "{}[]":
                lines.append(s)
        return lines