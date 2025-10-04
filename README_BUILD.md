# Todo应用打包指南

## 📦 使用PyInstaller打包（文件夹模式 - 推荐）

### 🚀 为什么选择文件夹模式？

**文件夹模式的优势：**
- ✅ **启动极快** - 无需解压，直接运行，速度和在开发环境中运行几乎一样
- ✅ **无闪退问题** - 启动速度快，不会触发系统超时
- ✅ **更好的调试体验** - 可以查看依赖文件，便于问题排查
- ✅ **更小的内存占用** - 不需要在内存中解压整个应用

**与单文件模式对比：**
| 特性 | 文件夹模式 | 单文件模式 |
|------|------------|------------|
| 启动速度 | ⚡ 极快 | 🐌 较慢（需要解压） |
| 文件大小 | 📁 较大（分散文件） | 📦 较小（压缩） |
| 调试难度 | 🔍 容易 | 😵 困难 |
| 分发方式 | 📁 整个文件夹 | 📄 单个文件 |

### 1. 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt

# 或者手动安装
pip install requests python-dotenv pyinstaller
```

### 2. 配置环境变量

创建 `.env` 文件（如果还没有）：

```bash
# .env 文件内容
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
TASKS_PATH=tasks.json
```

### 3. 打包方法

#### 方法一：使用自动化脚本（推荐）

```bash
python build.py
```

#### 方法二：使用spec文件

```bash
pyinstaller build.spec
```

#### 方法三：直接使用PyInstaller命令（文件夹模式）

```bash
pyinstaller \
  --windowed \
  --name=TodoApp \
  --icon=aioec-uf8e8.icns \
  --paths=. \
  --paths=logic \
  --paths=ui \
  --paths=style \
  --add-data=assets:assets \
  --add-data=tasks.json:. \
  --hidden-import=tkinter \
  --hidden-import=tkinter.ttk \
  --hidden-import=requests \
  --hidden-import=dotenv \
  --clean \
  ui/app.py
```

**注意：** 移除了 `--onefile` 选项，使用文件夹模式获得最佳性能。

### 4. 打包结果

**文件夹模式打包结果：**
```
dist/
└── TodoApp/                    # 应用程序文件夹
    ├── TodoApp                # 主可执行文件
    └── _internal/             # 依赖文件目录
        ├── assets/            # 资源文件
        ├── base_library.zip  # Python标准库
        ├── _tkinter.so       # Tkinter依赖
        └── ...               # 其他依赖文件
```

**运行应用：**
```bash
# 运行打包后的应用
./dist/TodoApp/TodoApp

# 或者直接双击 TodoApp 可执行文件
```

**分发方式：**
```bash
# 将整个文件夹打包成zip文件分发
zip -r TodoApp.zip dist/TodoApp/
```

### 6. 常见问题

#### 问题1：模块找不到
**解决方案：** 确保所有路径都包含在 `--paths` 选项中

#### 问题2：图标不显示
**解决方案：** 检查图标文件路径和格式
- macOS: `.icns` 格式
- Windows: `.ico` 格式
- Linux: `.png` 格式

#### 问题3：数据文件丢失
**解决方案：** 使用 `--add-data` 选项包含必要的数据文件

#### 问题4：字体文件找不到
**解决方案：** 确保 `assets/fonts/` 目录被正确包含

### 7. 优化建议

1. **减小文件大小：**
```bash
pyinstaller --onefile --windowed --strip --upx-dir=/path/to/upx ui/app.py
```

2. **调试模式：**
```bash
pyinstaller --onefile --console ui/app.py  # 显示控制台输出
```

3. **分析依赖：**
```bash
pyinstaller --onefile --debug=all ui/app.py
```

### 8. 分发准备

打包完成后，确保包含以下文件：
- 可执行文件
- `.env.example` 文件（用户配置模板）
- `README.md` 使用说明

### 9. 跨平台打包

- **macOS:** 在macOS上打包，生成 `.app` 或可执行文件
- **Windows:** 在Windows上打包，生成 `.exe` 文件
- **Linux:** 在Linux上打包，生成可执行文件

### 10. 代码签名（可选）

对于macOS应用分发：

```bash
# 代码签名
codesign --force --deep --sign "Developer ID Application: Your Name" dist/TodoApp

# 验证签名
codesign --verify --verbose dist/TodoApp
```
