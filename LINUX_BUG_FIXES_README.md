# ComfyUI-LatentSyncWrapper Linux 问题修复文档

## 概述

本文档记录了在 Linux 系统上运行 ComfyUI-LatentSyncWrapper 节点时遇到的主要问题及其修复方案。

## 问题列表

### 1. Hugging Face 模型缓存损坏问题

**问题描述**：
- `AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse")` 失败
- 错误：`OSError: Can't load config for 'stabilityai/sd-vae-ft-mse'`
- 缓存目录符号链接指向不存在的blob文件

**根本原因**：
- Hugging Face 缓存目录损坏或下载不完整
- 符号链接指向的blob文件不存在

**修复方案**：
```bash
# 清理损坏的缓存
rm -rf /home/george/.cache/huggingface/hub/models--stabilityai--sd-vae-ft-mse

# 重新下载模型
cd /home/george/ComfyUI && source venv/bin/activate && python -c "
from huggingface_hub import snapshot_download
snapshot_download('stabilityai/sd-vae-ft-mse')
"
```

### 2. FFmpeg 检测失败问题

**问题描述**：
- 节点初始化时 FFmpeg 检测失败
- 内部推理过程中 FFmpeg 检查失败

**根本原因**：
- `subprocess.run()` 使用 `check=True` 参数导致检测失败时抛出异常
- 没有多路径尝试机制

**修复文件**：
- `nodes.py` - `check_ffmpeg()` 函数
- `latentsync/utils/util.py` - `check_ffmpeg_installed()` 函数

**修复方案**：
```python
# 使用多路径尝试机制，不使用 check=True
ffmpeg_paths = ["/usr/bin/ffmpeg", "ffmpeg"]
for ffmpeg_cmd in ffmpeg_paths:
    try:
        result = subprocess.run([ffmpeg_cmd, "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            return True
    except Exception:
        continue
```

### 2. FFmpeg 路径继承问题

**问题描述**：
- FFmpeg 检测成功，但在 Whisper 音频处理阶段失败
- 错误：`FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**根本原因**：
- `ffmpeg-python` 库没有正确继承系统的 PATH 环境变量
- 直接使用 `["ffmpeg", "-nostdin"]` 而没有使用绝对路径

**修复文件**：
- `latentsync/whisper/whisper/audio.py`

**修复方案**：
```python
# 添加 FFmpeg 路径查找函数
def find_ffmpeg():
    ffmpeg_paths = ["/usr/bin/ffmpeg", "ffmpeg"]
    for ffmpeg_cmd in ffmpeg_paths:
        try:
            result = subprocess.run([ffmpeg_cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                return ffmpeg_cmd
        except Exception:
            continue
    raise FileNotFoundError("ffmpeg not found")

# 修改 load_audio 函数使用正确的路径
def load_audio(file: str, sr: int = SAMPLE_RATE):
    ffmpeg_cmd = find_ffmpeg()
    out, _ = (
        ffmpeg.input(file, threads=0)
        .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=sr)
        .run(cmd=[ffmpeg_cmd, "-nostdin"], capture_stdout=True, capture_stderr=True)
    )
```

### 3. 模型重复下载问题

**问题描述**：
- buffalo_l 模型文件已经存在，但 insightface 库仍然尝试重新下载
- 导致网络请求失败和性能问题

**根本原因**：
- insightface 库没有正确检测到本地已存在的模型文件
- 缺少环境变量控制机制

**修复文件**：
- `latentsync/utils/face_detector.py` - `FaceDetector.__init__()` 方法

**修复方案**：
```python
# 检查模型文件是否已存在
model_dir = os.path.join(wrapper_root, "checkpoints", "auxiliary", "models", "buffalo_l")
required_files = ["1k3d68.onnx", "2d106det.onnx", "det_10g.onnx", "genderage.onnx", "w600k_r50.onnx"]

all_files_exist = True
for file in required_files:
    file_path = os.path.join(model_dir, file)
    if not os.path.exists(file_path):
        all_files_exist = False
        break

# 设置环境变量控制 insightface 行为
if all_files_exist:
    os.environ['INSIGHTFACE_NO_DOWNLOAD'] = '1'
    os.environ['INSIGHTFACE_HOME'] = os.path.join(wrapper_root, "checkpoints", "auxiliary")
else:
    if 'INSIGHTFACE_NO_DOWNLOAD' in os.environ:
        del os.environ['INSIGHTFACE_NO_DOWNLOAD']
```

### 4. 路径计算问题

**问题描述**：
- 相对路径计算错误导致文件检测失败
- 在不同环境中路径解析不一致

**修复方案**：
```python
# 使用绝对路径计算
current_dir = os.path.dirname(os.path.abspath(__file__))
wrapper_root = os.path.dirname(os.path.dirname(current_dir))
model_dir = os.path.join(wrapper_root, "checkpoints", "auxiliary", "models", "buffalo_l")
```

## 修复总结

| 问题类型 | 修复文件 | 修复方法 |
|---------|---------|---------|
| FFmpeg 检测 | nodes.py, util.py | 多路径尝试 + 错误处理 |
| FFmpeg 路径继承 | audio.py | 添加路径查找函数 |
| 模型重复下载 | face_detector.py | 文件存在检查 + 环境变量控制 |
| 路径计算 | face_detector.py | 使用绝对路径计算 |

## 验证方法

1. **FFmpeg 检测**：节点初始化时应显示 "FFmpeg found at: /usr/bin/ffmpeg"
2. **模型下载**：如果模型文件已存在，应显示 "All buffalo_l model files already exist, preventing re-download"
3. **音频处理**：Whisper 音频处理应正常工作，不再出现 "No such file or directory: 'ffmpeg'" 错误

## 注意事项

1. 确保系统已安装 FFmpeg：`sudo apt install ffmpeg` 或 `conda install -c conda-forge ffmpeg`
2. 模型文件应放置在正确目录：`checkpoints/auxiliary/models/buffalo_l/`
3. 所有修复都保持了向后兼容性，不会影响其他系统的正常运行

## 版本信息

- **修复时间**：2025年8月25日
- **影响版本**：所有 ComfyUI-LatentSyncWrapper 版本
- **测试环境**：Linux Ubuntu, Python 3.12, ComfyUI

这些修复解决了在 Linux 系统上运行 LatentSyncWrapper 节点时的主要兼容性问题。
