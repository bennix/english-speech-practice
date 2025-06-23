#!/usr/bin/env python3
"""
英语视频复述练习评判系统 - 环境设置脚本
"""

import subprocess
import sys
import os
import platform
import urllib.request
import json

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    if sys.version_info < (3, 8):
        print("❌ 错误：需要Python 3.8或更高版本")
        print(f"   当前版本：{sys.version}")
        return False
    print(f"✅ Python版本检查通过：{sys.version}")
    return True

def check_ffmpeg():
    """检查FFmpeg是否安装"""
    print("🔍 检查FFmpeg...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg已安装")
            return True
        else:
            print("❌ FFmpeg未正确安装")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg未安装")
        print_ffmpeg_install_instructions()
        return False

def print_ffmpeg_install_instructions():
    """打印FFmpeg安装说明"""
    system = platform.system().lower()
    print("\n📦 FFmpeg安装说明：")
    
    if system == "windows":
        print("   Windows:")
        print("   1. 访问 https://ffmpeg.org/download.html")
        print("   2. 下载Windows版本并解压")
        print("   3. 将ffmpeg.exe路径添加到系统PATH")
        print("   或使用Chocolatey: choco install ffmpeg")
    elif system == "darwin":
        print("   macOS:")
        print("   使用Homebrew: brew install ffmpeg")
    else:
        print("   Linux:")
        print("   Ubuntu/Debian: sudo apt install ffmpeg")
        print("   CentOS/RHEL: sudo yum install ffmpeg")

def check_ollama():
    """检查Ollama是否安装和运行"""
    print("🔍 检查Ollama...")
    
    # 检查Ollama是否安装
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama已安装")
        else:
            print("❌ Ollama未正确安装")
            print_ollama_install_instructions()
            return False
    except FileNotFoundError:
        print("❌ Ollama未安装")
        print_ollama_install_instructions()
        return False
    
    # 检查Ollama服务是否运行
    try:
        response = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5)
        data = json.loads(response.read().decode())
        print("✅ Ollama服务正在运行")
        
        # 检查gemma2模型是否安装
        models = [model['name'] for model in data.get('models', [])]
        if any('gemma2' in model for model in models):
            print("✅ Gemma2模型已安装")
            return True
        else:
            print("⚠️  Gemma2模型未安装")
            print("   请运行: ollama pull gemma2")
            return False
            
    except Exception as e:
        print("❌ Ollama服务未运行")
        print("   请运行: ollama serve")
        return False

def print_ollama_install_instructions():
    """打印Ollama安装说明"""
    print("\n📦 Ollama安装说明：")
    print("   1. 访问 https://ollama.ai 下载安装")
    print("   2. 安装完成后运行: ollama serve")
    print("   3. 下载模型: ollama pull gemma2")

def install_python_dependencies():
    """安装Python依赖"""
    print("📦 安装Python依赖...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Python依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Python依赖安装失败：{e}")
        return False

def create_run_script():
    """创建运行脚本"""
    print("📝 创建运行脚本...")
    
    if platform.system().lower() == "windows":
        script_content = """@echo off
echo 启动英语视频复述练习评判系统...
python app.py
pause
"""
        with open("run.bat", "w", encoding="utf-8") as f:
            f.write(script_content)
        print("✅ 创建了run.bat启动脚本")
    else:
        script_content = """#!/bin/bash
echo "启动英语视频复述练习评判系统..."
python app.py
"""
        with open("run.sh", "w", encoding="utf-8") as f:
            f.write(script_content)
        os.chmod("run.sh", 0o755)
        print("✅ 创建了run.sh启动脚本")

def main():
    """主函数"""
    print("🎥 英语视频复述练习评判系统 - 环境设置")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 4
    
    # 检查Python版本
    if check_python_version():
        checks_passed += 1
    
    print()
    
    # 检查FFmpeg
    if check_ffmpeg():
        checks_passed += 1
    
    print()
    
    # 检查Ollama
    if check_ollama():
        checks_passed += 1
    
    print()
    
    # 安装Python依赖
    if install_python_dependencies():
        checks_passed += 1
    
    print()
    
    # 创建运行脚本
    create_run_script()
    
    print("\n" + "=" * 50)
    print(f"📊 环境检查完成：{checks_passed}/{total_checks} 项通过")
    
    if checks_passed == total_checks:
        print("🎉 所有检查通过！您可以运行应用了")
        print("\n启动方式：")
        print("   方法1: python app.py")
        if platform.system().lower() == "windows":
            print("   方法2: 双击 run.bat")
        else:
            print("   方法2: ./run.sh")
    else:
        print("⚠️  请解决上述问题后重新运行此脚本")
        print("   或查看README.md获取详细安装说明")

if __name__ == "__main__":
    main() 