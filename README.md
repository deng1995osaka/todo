## Todo (Task Decomposition)

An elegant, minimal desktop Todo app with automatic task decomposition powered by DeepSeek. Built with Python Tkinter and styled to resemble Apple Notes.

### Features
- **Task management**: add tasks, toggle completion
- **Task decomposition**: select a task and let DeepSeek generate Japanese subtasks
- **Hierarchical display**: parent tasks as checkboxes; subtasks as indented labels
- **Non-blocking UI**: decomposition runs in a background thread

### Project Structure
```
todo/
  ├─ assets/                 # Fonts & images (not strictly required by current UI)
  ├─ config.py               # API config and decomposition prompt
  ├─ main.py                 # Tkinter UI entry point
  └─ task_manager.py         # Task model and decomposition logic (reusable)
```

### Requirements
- macOS (or any desktop OS with Tkinter support)
- Python 3.9+
- Dependencies: `requests` (Tkinter ships with Python standard library)

Install dependencies:
```bash
pip install requests
```

### Configure DeepSeek
Edit `config.py` and set:
- `DEEPSEEK_API_KEY`: your API key
- `DEEPSEEK_API_URL`: `https://api.deepseek.com/v1/chat/completions`
- `DEEPSEEK_MODEL`: `deepseek-chat`

The default prompt instructs DeepSeek to reply in Japanese with a numbered bullet list. If you prefer Chinese or English output, update the prompt in `config.py` and the system message in `main.py`/`task_manager.py` accordingly.

Security note:
- Do not commit real API keys. Consider loading from environment variables instead:
```python
import os
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
```

### Run
```bash
python main.py
```

### How It Works
- `task_manager.py`
  - `Task`: dataclass with nested `subtasks` support
  - `TaskManager`: manages tasks, toggles completion, and performs asynchronous decomposition via DeepSeek
  - Response handling: attempts JSON parse first; if it fails, falls back to cleaning numbered bullet text
- `main.py`
  - Tkinter UI: input field, "タスク追加" button, task list, and "分解" button
  - Selecting a task highlights it; clicking "分解" attaches generated subtasks under the selected task

### Usage
1. Type a task name at the top and click "タスク追加"
2. Click a parent task to select it (highlighted background)
3. Click "分解" to generate Japanese subtasks via DeepSeek
4. Toggle the checkbox to mark a parent task done/undone

### Troubleshooting
- **No response / network error**: verify `DEEPSEEK_API_KEY` and internet access to `api.deepseek.com`
- **Output not in JSON**: the app automatically cleans numbered bullet lines
- **Language**: change prompt and system messages to your preferred language

### Roadmap
- Persist tasks (current data is in-memory only)
- Delete tasks and drag-and-drop ordering
- Language switcher (ZH/JA/EN)
- Enhanced UI using assets

### License
For learning and personal use only. Check third-party API and asset licenses for commercial usage.


