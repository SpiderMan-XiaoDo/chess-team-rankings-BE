"""Utilities function"""
import re
import hashlib
from flask import request

def decode_html_entities(s: str) -> str:
    """Decode html entities"""
    return re.sub(r'&#(\d+);', lambda match: chr(int(match.group(1))), s)

def find_object_with_key_value(lst, key, value):
    """Find object with key value"""
    for obj in lst:
        if obj.get(key) == value:
            return obj
    return None

def make_cache_key():
    """Tạo khóa cache dựa trên URL và nội dung của yêu cầu POST"""
    data = request.get_data()  # Lấy nội dung của yêu cầu POST
    return hashlib.md5(data).hexdigest()  # Tạo chuỗi hash duy nhất từ nội dung
