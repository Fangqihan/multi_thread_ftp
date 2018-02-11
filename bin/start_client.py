# -*- coding: utf-8 -*-   @Time    : 18-1-25 下午4:41
# @Author  : QiHanFang    @Email   : qihanfang@foxmail.com
# 先启动 服务器start_server.py, 再启动客户端start_client.py文件

import os
import sys


PRO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PRO_DIR)

from core.client import run_client
run_client()











