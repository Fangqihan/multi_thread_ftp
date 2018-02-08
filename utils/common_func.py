# -*- coding: utf-8 -*-   @Time    : 18-1-26 上午10:35
# @Author  : QiHanFang    @Email   : qihanfang@foxmail.com
import hashlib
from conf.settings import *


def get_file_md5(file_path):
    """将文件进行加密,取得MD5值"""
    m = hashlib.md5()
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        size = 0
        while size <= file_size:
            m.update(f.read(8192))
            size += 8192

    return m.hexdigest()
