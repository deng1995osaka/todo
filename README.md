# Todo (Task Decomposition)

*A minimal desktop Todo app with automatic task decomposition powered by DeepSeek*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/Tkinter-GUI-lightgrey.svg)](https://docs.python.org/3/library/tkinter.html)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-API-orange.svg)](https://deepseek.com/)
[![License](https://img.shields.io/badge/license-Learning%20Use-green.svg)](#license)

An elegant, Apple Notes–style desktop Todo app.
Write tasks, click **分解**, and let **DeepSeek** generate subtasks in Japanese (or any language you configure).

---

## ✨ Features

* **Task management** — add tasks, toggle completion
* **Task decomposition** — generate subtasks via DeepSeek
* **Hierarchical view** — parent tasks (checkboxes), subtasks (indented labels)
* **Responsive UI** — background threading prevents blocking

---

## 🗂 Project Structure

```text
todo/
  ├─ assets/          # Fonts & images (optional)
  ├─ config.py        # API config & decomposition prompt
  ├─ main.py          # Tkinter UI entry point
  └─ task_manager.py  # Task model & decomposition logic
```

---

## ⚙️ Requirements

* **OS:** macOS / Linux / Windows (Tkinter supported)
* **Python:** 3.9+
* **Dependencies:** `requests`

Install deps:

```bash
pip install requests
```

---

## 🔑 Configure DeepSeek

Edit `config.py`:

* `DEEPSEEK_API_KEY` — your API key
* `DEEPSEEK_API_URL` — `https://api.deepseek.com/v1/chat/completions`
* `DEEPSEEK_MODEL` — `deepseek-chat`

Default prompt outputs Japanese subtasks (numbered list).
Change prompt in `config.py` + system message in `main.py`/`task_manager.py` to switch language.

**Security tip:**

```python
import os
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
```

---

## ▶️ Run

```bash
python main.py
```

---

## 🛠 How It Works

* **task\_manager.py**

  * `Task`: dataclass with nested `subtasks`
  * `TaskManager`: add/toggle tasks, async decomposition via DeepSeek
  * Response: try JSON parse → fallback to clean numbered bullets
* **main.py**

  * Tkinter UI with input field, "タスク追加" button, task list, and "分解" button
  * Selected task highlights; generated subtasks attach beneath

---

## 📒 Usage

1. Type a task → click **タスク追加**
2. Select a parent task (highlighted)
3. Click **分解** → DeepSeek generates subtasks
4. Toggle checkbox → mark task done/undone

---

## 🐞 Troubleshooting

* **No response / network error:** check API key & internet access
* **Non-JSON output:** app auto-cleans numbered bullet lines
* **Wrong language:** update prompt/system messages

---

## 🛤 Roadmap

* Save tasks (persistent storage)
* Delete & reorder tasks (drag-and-drop)
* Language switcher (ZH/JA/EN)
* Enhanced UI with assets

---

## 📜 License

For **learning & personal use only**.
Check third-party API & asset licenses for commercial projects.

---

