#!/usr/bin/env python3
"""
PyInstaller 打包脚本
用于将Todo应用打包为可执行文件
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主打包函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.absolute()
    
    # 定义路径
    paths = [
        str(project_root),                    # 根目录
        str(project_root / "logic"),          # 业务逻辑模块
        str(project_root / "ui"),             # UI模块
        str(project_root / "style"),          # 样式模块
    ]
    
    # 图标文件路径
    icon_path = project_root / "aioec-uf8e8.icns"
    
    # 主程序入口
    main_script = project_root / "ui" / "app.py"
    
    # 构建PyInstaller命令
    cmd = [
        "pyinstaller",
        # "--onefile",                        # 注释掉：使用文件夹模式获得更好性能
        "--windowed",                         # 无控制台窗口（GUI应用）
        "--name=TodoApp",                     # 可执行文件名称
        f"--icon={icon_path}",               # 图标文件
        "--add-data=assets:assets",          # 包含assets目录
        "--add-data=tasks.json:.",           # 包含数据文件
        "--hidden-import=tkinter",            # 确保tkinter被包含
        "--hidden-import=tkinter.ttk",       # 确保ttk被包含
        "--hidden-import=requests",           # 确保requests被包含
        "--hidden-import=dotenv",             # 确保python-dotenv被包含
        "--clean",                            # 清理临时文件
    ]
    
    # 添加所有路径到--paths
    for path in paths:
        cmd.extend(["--paths", path])
    
    # 添加主脚本
    cmd.append(str(main_script))
    
    print("🚀 开始打包Todo应用...")
    print(f"📁 项目根目录: {project_root}")
    print(f"🎨 图标文件: {icon_path}")
    print(f"📝 主脚本: {main_script}")
    print(f"📂 包含路径: {paths}")
    print()
    
    # 检查必要文件是否存在
    if not icon_path.exists():
        print(f"❌ 错误: 图标文件不存在: {icon_path}")
        return 1
    
    if not main_script.exists():
        print(f"❌ 错误: 主脚本不存在: {main_script}")
        return 1
    
    # 执行打包命令
    try:
        print("📦 执行PyInstaller命令...")
        print(" ".join(cmd))
        print()
        
        result = subprocess.run(cmd, check=True, cwd=project_root)
        
        print("✅ 打包完成!")
        print(f"📦 应用程序文件夹: {project_root / 'dist' / 'TodoApp'}")
        print(f"🚀 可执行文件: {project_root / 'dist' / 'TodoApp' / 'TodoApp'}")
        print()
        print("💡 文件夹模式的优势:")
        print("   ✅ 启动极快 - 无需解压，直接运行")
        print("   ✅ 无闪退问题 - 启动速度快，不会触发系统超时")
        print("   ✅ 更好的调试体验 - 可以查看依赖文件")
        print("   📁 分发方式: 将整个TodoApp文件夹打包成zip文件分发")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        return 1
    except FileNotFoundError:
        print("❌ 错误: 未找到PyInstaller，请先安装:")
        print("pip install pyinstaller")
        return 1

if __name__ == "__main__":
    sys.exit(main())
