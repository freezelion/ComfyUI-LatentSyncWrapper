# ComfyUI-LatentSyncWrapper Linux 兼容性修复

## 概述

此分支包含了针对 Linux 系统的 ComfyUI-LatentSyncWrapper 节点的兼容性修复。原始代码在 Windows 环境下开发，在 Linux 系统上运行时遇到了多个兼容性问题。

## 修复内容

### 1. Hugging Face 模型加载问题
- **问题**: `AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse")` 失败
- **修复**: 清理损坏的缓存并重新下载模型
- **文件**: 无需代码修改，需要执行清理命令

### 2. FFmpeg 路径继承问题
- **问题**: `ffmpeg-python` 库无法正确继承系统 PATH
- **修复**: 添加 FFmpeg 路径查找函数，使用绝对路径
- **文件**: 
  - `latentsync/whisper/whisper/audio.py`
  - `latentsync/utils/util.py`
  - `latentsync/pipelines/lipsync_pipeline.py`

### 3. 模型重复下载问题
- **问题**: insightface 库重复下载已存在的模型文件
- **修复**: 添加文件存在性检查和环境变量控制
- **文件**: `latentsync/utils/face_detector.py`

### 4. 路径计算问题
- **问题**: 相对路径在不同环境中解析不一致
- **修复**: 使用绝对路径计算
- **文件**: `latentsync/utils/face_detector.py`

## 环境要求

### 系统要求
- **操作系统**: Linux (Ubuntu/Debian/CentOS等)
- **Python**: 3.8+
- **ComfyUI**: 最新版本

### 依赖安装
```bash
# 安装 FFmpeg
sudo apt update
sudo apt install ffmpeg

# 或使用 conda
conda install -c conda-forge ffmpeg

# 安装 Python 依赖
pip install -r requirements.txt
```

### 模型文件
确保以下模型文件已正确放置：
- `checkpoints/auxiliary/models/buffalo_l/` 目录下的所有 .onnx 文件
- `checkpoints/latentsync_unet.pt`
- `checkpoints/whisper/tiny.pt`

## 使用说明

1. **首次运行前**:
   ```bash
   # 清理可能损坏的 Hugging Face 缓存
   rm -rf ~/.cache/huggingface/hub/models--stabilityai--sd-vae-ft-mse
   ```

2. **正常使用**:
   - 节点会自动检测和修复 FFmpeg 路径问题
   - 模型文件存在时会避免重复下载
   - 所有路径计算使用绝对路径确保一致性

## 兼容性说明

- **向后兼容**: 所有修复都保持了与原始代码的兼容性
- **跨平台**: 修复只在 Linux 环境下生效，不影响其他系统
- **性能**: 修复不会影响节点性能，反而通过避免重复下载提升了效率

## 验证方法

运行节点后检查日志：
- `FFmpeg found at: /usr/bin/ffmpeg` - FFmpeg 检测成功
- `All buffalo_l model files already exist, preventing re-download` - 模型文件检查成功
- 无 `FileNotFoundError: 'ffmpeg'` 错误 - FFmpeg 路径继承成功

## 贡献

这些修复针对 Linux 环境特有的问题，如果您在其他 Linux 发行版上遇到类似问题，欢迎提交 Issue 或 Pull Request。

## 许可证

与原项目保持一致，详见 LICENSE 文件。

## 维护者

- 修复由 AI 助手完成，专门解决 Linux 兼容性问题
- 文档更新于 2025年8月25日

## 版本兼容性

- **ComfyUI 版本**: 基于 commit `56b36205` (2024年5月21日)
- **LatentSyncWrapper 版本**: 基于原作者的最近版本 + Linux 修复
- **Python 版本**: 3.8+
- **系统支持**: Linux Ubuntu/Debian/CentOS

## 标签

`linux-support` `compatibility-fixes` `ffmpeg-fix` `huggingface-fix`
