import gradio as gr
import whisper
import requests
import json
import tempfile
import os
from pathlib import Path
import subprocess
import librosa
import soundfile as sf
from typing import Tuple, Optional
import time
import config

class EnglishPracticeApp:
    def __init__(self):
        # 加载Whisper模型
        print("正在加载Whisper模型...")
        self.whisper_model = whisper.load_model(config.WHISPER_MODEL)
        print("Whisper模型加载完成")
        
        # Ollama API配置
        self.ollama_url = config.OLLAMA_URL
        self.model_name = config.OLLAMA_MODEL
        
        # 支持的音频格式
        self.audio_formats = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma']
        # 支持的视频格式
        self.video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    def is_audio_file(self, file_path: str) -> bool:
        """检查文件是否为音频格式"""
        if not file_path:
            return False
        ext = Path(file_path).suffix.lower()
        return ext in self.audio_formats
    
    def is_video_file(self, file_path: str) -> bool:
        """检查文件是否为视频格式"""
        if not file_path:
            return False
        ext = Path(file_path).suffix.lower()
        return ext in self.video_formats
        
    def extract_audio_from_video(self, video_path: str) -> str:
        """从视频文件中提取音频"""
        try:
            # 创建临时音频文件
            temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_audio.close()
            
            # 使用ffmpeg提取音频
            cmd = [
                "ffmpeg", 
                "-i", video_path,
                "-ac", str(config.AUDIO_CHANNELS),
                "-ar", str(config.AUDIO_SAMPLE_RATE),
                "-y",  # 覆盖输出文件
                temp_audio.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return temp_audio.name
            else:
                raise Exception(f"音频提取失败: {result.stderr}")
                
        except Exception as e:
            raise Exception(f"提取音频时出错: {str(e)}")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """使用Whisper转录音频"""
        try:
            if config.VERBOSE_LOGGING:
                print(f"正在转录音频: {audio_path}")
            
            result = self.whisper_model.transcribe(audio_path)
            # 修复：确保text是字符串类型
            text = str(result["text"]).strip()
            
            if config.VERBOSE_LOGGING:
                print(f"转录结果: {text}")
            return text
        except Exception as e:
            raise Exception(f"音频转录失败: {str(e)}")
    
    def process_media_file(self, media_file) -> Tuple[str, str]:
        """处理上传的媒体文件（视频或音频）"""
        if media_file is None:
            return "请上传音频或视频文件", ""
        
        try:
            file_path = media_file
            file_name = Path(file_path).name
            
            # 检查文件类型
            if self.is_audio_file(file_path):
                # 直接处理音频文件
                if config.VERBOSE_LOGGING:
                    print(f"检测到音频文件: {file_name}")
                
                transcribed_text = self.transcribe_audio(file_path)
                return f"音频文件 '{file_name}' 处理完成！", transcribed_text
                
            elif self.is_video_file(file_path):
                # 处理视频文件（提取音频后转录）
                if config.VERBOSE_LOGGING:
                    print(f"检测到视频文件: {file_name}")
                
                # 提取音频
                audio_path = self.extract_audio_from_video(file_path)
                
                # 转录音频
                transcribed_text = self.transcribe_audio(audio_path)
                
                # 清理临时文件
                if config.AUTO_CLEANUP_TEMP_FILES and os.path.exists(audio_path):
                    os.unlink(audio_path)
                
                return f"视频文件 '{file_name}' 处理完成！", transcribed_text
            else:
                return f"不支持的文件格式。请上传音频文件（{', '.join(self.audio_formats)}）或视频文件（{', '.join(self.video_formats)}）", ""
            
        except Exception as e:
            return f"处理文件时出错: {str(e)}", ""
    
    def transcribe_user_audio(self, audio_file) -> Tuple[str, str]:
        """转录用户录制的音频"""
        if audio_file is None:
            return "请录制您的复述音频", ""
        
        try:
            # 转录用户音频
            user_text = self.transcribe_audio(audio_file)
            return "音频转录完成！", user_text
            
        except Exception as e:
            return f"转录用户音频时出错: {str(e)}", ""
    
    def evaluate_speech(self, original_text: str, user_text: str) -> str:
        """使用Ollama评判用户复述质量"""
        if not original_text or not user_text:
            return "请确保已完成视频转录和用户音频录制"
        
        try:
            # 构建评判提示词
            weights = config.SCORING_WEIGHTS
            prompt = f"""
请作为一名严格的英语教师，对学生的英语复述进行评判。请用Markdown格式回答。

**原始文本：**
{original_text}

**学生复述：**
{user_text}

请从以下几个维度进行评分（满分100分）：

1. 内容准确性 ({weights['content_accuracy']}分): 复述内容与原文的匹配程度
2. 语法正确性 ({weights['grammar']}分): 语法结构的准确性
3. 词汇使用 ({weights['vocabulary']}分): 词汇选择的准确性和丰富性
4. 流利度 ({weights['fluency']}分): 语言表达的流畅程度
5. 完整性 ({weights['completeness']}分): 复述的完整程度

请按照以下Markdown格式给出评判：

## 学生复述评判

**总分: X/100**

### 详细评分：

**1. 内容准确性 (X/{weights['content_accuracy']}分)**
评判理由...

**2. 语法正确性 (X/{weights['grammar']}分)**
评判理由...

**3. 词汇使用 (X/{weights['vocabulary']}分)**
评判理由...

**4. 流利度 (X/{weights['fluency']}分)**
评判理由...

**5. 完整性 (X/{weights['completeness']}分)**
评判理由...

### 🎯 改进建议：
- 建议1
- 建议2
- 建议3

### 👍 表现良好的地方：
- 优点1
- 优点2

评判标准要严格，按照高标准要求。请严格用中文回答，使用Markdown格式。
"""

            # 调用Ollama API
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            if config.VERBOSE_LOGGING:
                print("正在连接Ollama进行评判...")
            
            response = requests.post(
                self.ollama_url, 
                json=payload, 
                timeout=config.OLLAMA_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                evaluation = result.get("response", "评判失败")
                return evaluation
            else:
                return f"Ollama连接失败，状态码: {response.status_code}\n请确保Ollama服务正在运行并且已安装{self.model_name}模型"
                
        except requests.exceptions.ConnectionError:
            return f"无法连接到Ollama服务。请确保：\n1. Ollama服务正在运行\n2. 使用命令 'ollama serve' 启动服务\n3. 使用命令 'ollama pull {self.model_name}' 下载模型"
        except Exception as e:
            return f"评判过程中出错: {str(e)}"

# 创建应用实例
app = EnglishPracticeApp()

def update_evaluation_display(evaluation_text):
    """更新评判结果显示，返回格式化的Markdown内容"""
    if not evaluation_text or evaluation_text.strip() == "":
        return "📝 评判结果将在这里显示..."
    
    # 如果评判结果不是错误信息，添加一些格式化
    if not evaluation_text.startswith("请确保") and not evaluation_text.startswith("无法连接") and not evaluation_text.startswith("Ollama连接失败") and not evaluation_text.startswith("评判过程中出错"):
        # 添加标题和格式化
        formatted_text = f"""## 📊 AI评判结果

{evaluation_text}

---
*评判完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return formatted_text
    else:
        # 错误信息也格式化一下
        return f"""## ⚠️ 提示

{evaluation_text}
"""

# 创建Gradio界面
def create_interface():
    with gr.Blocks(title="英语音视频复述练习评判系统", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎥🎵 英语音视频复述练习评判系统
        
        这个应用可以帮助您练习英语听说能力：
        1. **上传音频或视频文件**，系统将自动转录成文字
        2. **录制您的复述音频**
        3. **AI严格评判**您的复述质量（100分制）
        
        **支持的格式：**
        - 🎵 **音频格式**: MP3, WAV, FLAC, M4A, AAC, OGG, WMA
        - 🎥 **视频格式**: MP4, AVI, MOV, MKV, WMV, FLV, WebM
        
        **使用前请确保：**
        - 已安装FFmpeg（用于视频处理）
        - Ollama服务正在运行：`ollama serve`
        - 已下载模型：`ollama pull gemma2`
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. 上传音频或视频文件")
                media_input = gr.File(
                    label="选择音频/视频文件或拖拽到此处",
                    file_types=["audio", "video"],
                    file_count="single"
                )
                process_btn = gr.Button("开始处理文件", variant="primary")
                processing_status = gr.Textbox(label="处理状态", interactive=False)
                
            with gr.Column(scale=1):
                gr.Markdown("### 2. 原始转录文本")
                original_text = gr.Textbox(
                    label="原始文本",
                    lines=8,
                    placeholder="音频/视频转录文本将在这里显示...",
                    interactive=False
                )
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 3. 录制您的复述")
                audio_input = gr.Audio(
                    label="点击录制您的复述",
                    sources=["microphone"],
                    type="filepath"
                )
                transcribe_btn = gr.Button("转录复述音频", variant="secondary")
                audio_status = gr.Textbox(label="转录状态", interactive=False)
                
            with gr.Column(scale=1):
                gr.Markdown("### 4. 您的复述文本")
                user_text = gr.Textbox(
                    label="复述文本",
                    lines=8,
                    placeholder="您的复述转录文本将在这里显示...",
                    interactive=False
                )
        
        gr.Markdown("### 5. AI评判结果")
        evaluate_btn = gr.Button("开始评判", variant="primary", size="lg")
        
        # 改为Markdown组件来正确渲染格式
        evaluation_result = gr.Markdown(
            value="📝 评判结果将在这里显示...",
            visible=True
        )
        
        # 定义评判处理函数
        def handle_evaluation(original_text, user_text):
            evaluation = app.evaluate_speech(original_text, user_text)
            formatted_result = update_evaluation_display(evaluation)
            return formatted_result
        
        # 绑定事件
        process_btn.click(
            fn=app.process_media_file,
            inputs=[media_input],
            outputs=[processing_status, original_text]
        )
        
        transcribe_btn.click(
            fn=app.transcribe_user_audio,
            inputs=[audio_input],
            outputs=[audio_status, user_text]
        )
        
        evaluate_btn.click(
            fn=handle_evaluation,
            inputs=[original_text, user_text],
            outputs=[evaluation_result]
        )
        
        gr.Markdown(f"""
        ---
        ### 使用提示：
        - 📁 **支持格式广泛**：常见的音频和视频格式都支持
        - 🎤 **录制建议**：录制音频时请保持环境安静
        - 🤖 **当前模型**：Whisper({config.WHISPER_MODEL}) + {config.OLLAMA_MODEL}
        - 📊 **评判标准**：严格的100分制评分
        - 🔧 **问题排查**：如遇问题，请检查依赖环境是否正确安装
        
        ### 🎯 使用建议：
        - **音频文件**：直接上传MP3、WAV等音频文件，转录速度更快
        - **视频文件**：支持MP4、AVI等视频文件，系统会自动提取音频
        - **文件大小**：建议文件大小在100MB以内，过大文件处理时间较长
        """)
    
    return demo

if __name__ == "__main__":
    # 检查依赖
    print("正在启动英语视频复述练习评判系统...")
    
    if config.DEBUG_MODE:
        print("调试模式已启用")
    
    demo = create_interface()
    demo.launch(
        share=config.GRADIO_SHARE,
        server_name=config.GRADIO_SERVER_NAME,
        server_port=config.GRADIO_SERVER_PORT,
        show_error=True
    ) 