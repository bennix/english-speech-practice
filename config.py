# 配置文件 - 英语视频复述练习评判系统

# Whisper模型配置
WHISPER_MODEL = "base"  # 可选: tiny, base, small, medium, large
# tiny: 最快但准确度较低
# base: 平衡速度和准确度（推荐）
# small: 较慢但准确度较高
# medium/large: 最慢但准确度最高

# Ollama配置
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma2"  # 模型名称，可根据需要更改

# Gradio界面配置
GRADIO_SERVER_NAME = "0.0.0.0"  # 设置为 "127.0.0.1" 仅本地访问
GRADIO_SERVER_PORT = 7860
GRADIO_SHARE = True  # 是否生成公开链接

# 评判标准权重（总和应为100）
SCORING_WEIGHTS = {
    "content_accuracy": 30,    # 内容准确性
    "grammar": 25,            # 语法正确性
    "vocabulary": 20,         # 词汇使用
    "fluency": 15,           # 流利度
    "completeness": 10       # 完整性
}

# 音频处理配置
AUDIO_SAMPLE_RATE = 16000  # 音频采样率
AUDIO_CHANNELS = 1         # 音频声道数（1=单声道）

# 临时文件清理
AUTO_CLEANUP_TEMP_FILES = True  # 是否自动清理临时文件

# 超时设置（秒）
OLLAMA_TIMEOUT = 60        # Ollama API超时时间
WHISPER_TIMEOUT = 300      # Whisper转录超时时间

# 调试设置
DEBUG_MODE = False         # 是否启用调试模式
VERBOSE_LOGGING = True     # 是否启用详细日志 