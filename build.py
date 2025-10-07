#!/usr/bin/env python3


import os
import sys
import subprocess
from pathlib import Path

def main():
    """ Main packaging function"""
    # Get project root directory
    project_root = Path(__file__).parent.absolute()
    
    
    paths = [
        str(project_root),                   
        str(project_root / "logic"),         
        str(project_root / "ui"),           
        str(project_root / "style"),         
    ]
    
    # Icon file path
    icon_path = project_root / "aioec-uf8e8.icns"
    
    # Main script entry point
    main_script = project_root / "ui" / "app.py"
    
    # PyInstaller commandの構築 
    cmd = [
        "pyinstaller",
        # "--onefile",                       
        "--windowed",                         # console window無し（GUIアプリ）
        "--name=TodoApp",                     # 実行ファイル名 
        f"--icon={icon_path}",               # Icon file
        "--add-data=assets:assets",          # assets directoryを含める
        f"--add-data={project_root / '.env'}:.",  # .env fileを含める（绝对路径） 
        "--hidden-import=tkinter",            # tkinterを含める 
        "--hidden-import=tkinter.ttk",       # ttkを含める 
        "--hidden-import=requests",           # requestsを含める 
        "--hidden-import=dotenv",             # python-dotenvを含める 
        "--clean",                            # Clean temporary files
        "--noconfirm",                        # Overwrite existing output without prompt
    ]
    
    # すべてのパスを --paths に追加 
    for path in paths:
        cmd.extend(["--paths", path])
    
    # Add main script
    cmd.append(str(main_script))
    
    print("🚀 Todoアプリのパッケージングを開始... / Start packaging Todo app...")
    print(f"📁 プロジェクトルート: {project_root} / Project root")
    print(f"🎨 アイコンファイル: {icon_path} / Icon file")
    print(f"📝 メインスクリプト: {main_script} / Main script")
    print(f"📂 含めるパス: {paths} / Included paths")
    print()
    
    # 必要なファイルが存在するかチェック 
    if not icon_path.exists():
        print(f"❌ エラー: アイコンファイルが存在しません: {icon_path} / Error: Icon file does not exist")
        return 1
    
    if not main_script.exists():
        print(f"❌ エラー: メインスクリプトが存在しません: {main_script} / Error: Main script does not exist")
        return 1
    
    # packaging commandを実行 
    try:
        print("📦 PyInstallerコマンドを実行... / Execute PyInstaller command...")
        print(" ".join(cmd))
        print()
        
        result = subprocess.run(cmd, check=True, cwd=project_root)
        
        print("✅ パッケージング完了! / Packaging complete!")
        print(f"📦 アプリフォルダ: {project_root / 'dist' / 'TodoApp'} / App folder")
        print(f"🚀 実行ファイル: {project_root / 'dist' / 'TodoApp' / 'TodoApp'} / Executable")
        print()
        print("💡 フォルダーモードの利点 / Advantages of folder mode:")
        print("   ✅ 起動が非常に速い - 解凍不要、直接実行 ")
        print("   ✅ crashesなし - 起動が速く、system timeoutを回避 ")
        print("   ✅ より良いdebugging体験 - 依存ファイルを確認できる ")
        print("   📁 配布方法: TodoAppフォルダ全体をzipにして配布 ")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ パッケージング失敗: {e} / Packaging failed")
        return 1
    except FileNotFoundError:
        print("❌ エラー: PyInstallerが見つかりません。先にインストールしてください: / Error: PyInstaller not found. Please install first:")
        print("pip install pyinstaller")
        return 1

if __name__ == "__main__":
    sys.exit(main())
