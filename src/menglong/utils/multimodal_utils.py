"""
多模态工具函数

提供文件加载、编码、类型检测等辅助功能。
"""

import base64
import mimetypes
from pathlib import Path
from typing import Tuple, Optional


# 文件大小限制 (字节)
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB (OpenAI 限制)
MAX_DOCUMENT_SIZE = 32 * 1024 * 1024  # 32MB (Anthropic 限制)
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB (Gemini Vertex AI 限制)

# MIME 类型映射
MIME_TYPES = {
    # 图片
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp',
    
    # 文档
    '.pdf': 'application/pdf',
    '.txt': 'text/plain',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    
    # 音频
    '.mp3': 'audio/mp3',
    '.wav': 'audio/wav',
    '.m4a': 'audio/m4a',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.aac': 'audio/aac',
    
    # 视频
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
    '.webm': 'video/webm',
    '.mkv': 'video/x-matroska',
}


def detect_media_type(file_path: str) -> str:
    """
    自动检测文件的 MIME 类型。
    
    Args:
        file_path: 文件路径
        
    Returns:
        MIME 类型字符串
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    # 优先使用自定义映射
    if suffix in MIME_TYPES:
        return MIME_TYPES[suffix]
    
    # 回退到 mimetypes 库
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    
    # 默认返回二进制类型
    return 'application/octet-stream'


def validate_file_size(file_path: str, max_size: int) -> None:
    """
    验证文件大小是否在限制内。
    
    Args:
        file_path: 文件路径
        max_size: 最大文件大小(字节)
        
    Raises:
        ValueError: 文件大小超过限制
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_size = path.stat().st_size
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"文件大小 ({actual_mb:.2f}MB) 超过限制 ({max_mb:.2f}MB): {file_path}"
        )


def load_file_as_base64(file_path: str) -> str:
    """
    将文件加载并编码为 Base64 字符串。
    
    Args:
        file_path: 文件路径
        
    Returns:
        Base64 编码的字符串
    """
    path = Path(file_path)
    with path.open('rb') as f:
        file_data = f.read()
    return base64.b64encode(file_data).decode('utf-8')


def load_image_from_path(file_path: str) -> Tuple[str, str]:
    """
    从本地路径加载图片并转为 Base64。
    
    Args:
        file_path: 图片文件路径
        
    Returns:
        (base64_data, media_type) 元组
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件大小超过限制
    """
    validate_file_size(file_path, MAX_IMAGE_SIZE)
    media_type = detect_media_type(file_path)
    data = load_file_as_base64(file_path)
    return data, media_type


def load_document_from_path(file_path: str) -> Tuple[str, str]:
    """
    从本地路径加载文档并转为 Base64。
    
    Args:
        file_path: 文档文件路径
        
    Returns:
        (base64_data, media_type) 元组
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件大小超过限制
    """
    validate_file_size(file_path, MAX_DOCUMENT_SIZE)
    media_type = detect_media_type(file_path)
    data = load_file_as_base64(file_path)
    return data, media_type


def load_audio_from_path(file_path: str) -> Tuple[str, str]:
    """
    从本地路径加载音频并转为 Base64。
    
    Args:
        file_path: 音频文件路径
        
    Returns:
        (base64_data, media_type) 元组
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件大小超过限制
    """
    validate_file_size(file_path, MAX_AUDIO_SIZE)
    media_type = detect_media_type(file_path)
    data = load_file_as_base64(file_path)
    return data, media_type


def load_video_from_path(file_path: str) -> Tuple[str, str]:
    """
    从本地路径加载视频并转为 Base64。
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        (base64_data, media_type) 元组
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件大小超过限制
    """
    validate_file_size(file_path, MAX_VIDEO_SIZE)
    media_type = detect_media_type(file_path)
    data = load_file_as_base64(file_path)
    return data, media_type


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读格式。
    
    Args:
        size_bytes: 文件大小(字节)
        
    Returns:
        格式化的字符串,如 "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
