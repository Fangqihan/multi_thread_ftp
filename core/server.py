# -*- coding: utf-8 -*-   @Time    : 18-2-8 下午5:11
# @Author  : QiHanFang    @Email   : qihanfang@foxmail.com

from socket import *
from threading import current_thread
import queue
import json
import struct
from threading import Thread

from conf.settings import *
from utils.common_func import get_file_md5, collect

login_user_lst = []
q = queue.Queue(MAX_THREADS)  # 设置最大线程数量


def receive(conn, username):
    """接收客户端发过来的文件,并保存至服务器的设定的存储文件夹下"""
    print('当前线程<%s>'%current_thread().name)
    while True:
        header_size_obj = conn.recv(4)
        if header_size_obj.decode('utf-8') == CHOICE_FLAG:
            # 检查是否是返回主界面命令
            print('接收到服务端返回主界面')
            break

        if not header_size_obj:
            collect(conn, q, login_user_lst, username)
            break
        # 获取header长度
        header_obj_size = struct.unpack('i', header_size_obj)[0]
        # 获取header信息
        header_obj_json = conn.recv(header_obj_size).decode('utf8')
        header_obj_dict = json.loads(header_obj_json)
        print('header_obj_dict: ', header_obj_dict)
        filename = header_obj_dict.get('filename', '')
        total_size = header_obj_dict.get('size', '')
        old_md5 = header_obj_dict.get('md5', '')
        # 逐行接收服务端返回的文件
        recv_size = 0
        save_path = '%s%s' % (SERVER_UPLOAD_DIR, filename)
        with open(save_path, 'wb') as f:
            while recv_size < total_size:
                rec1 = conn.recv(8888)
                f.write(rec1)
                recv_size += len(rec1)
            print('文件上传进度进度:{:.2f}%'.format(recv_size / total_size * 100), flush=True, end='\r')

        # 源文件和下载后文件一致性检验
        new_md5 = get_file_md5(save_path)
        file_check = ''
        if new_md5 == old_md5:
            file_check = '一致性匹配合格'
        else:
            file_check = '服务端发送的文件与收到的文件不一致'
        result_dic = {'file_check':file_check, 'upload_status':recv_size / total_size}
        result_str = json.dumps(result_dic)
        result_bytes = json.dumps(result_dic).encode('utf-8')
        result_size = struct.pack('i', len(result_str))
        conn.send(result_size)
        conn.send(result_bytes)
        break


def transfer(conn, username):
    """接收客户端选定的要下载的文件路径,并且将对应的文件传送给客户端"""
    print('线程<%s>开始准备下载'%current_thread().name)
    while True:
        file_path = conn.recv(8000)  # 接收客户端选定的文件路径
        if file_path == CHOICE_FLAG:  # 检查是否是返回主界面命令
            print('接收到服务端返回主界面')
            break
        if not file_path:
            collect(conn, q, login_user_lst, username)
            break
        file_path = file_path.decode('utf-8').strip()
        print(file_path)
        filename = file_path.split('/')[-1]
        try:
            file_size = os.path.getsize(file_path)
        except Exception:
            print('文件名称有误')
        # 制作文件的header信息
        header = {
            'filename': filename,
            'md5': get_file_md5(file_path),
            'size': file_size,
        }
        header_obj = json.dumps(header)  # 序列化成str类型
        header_obj_bytes = header_obj.encode('utf-8')
        # 将报头字节大小制作成定长字节串并发送给客户端
        header_obj_size = struct.pack('i', len(header_obj_bytes))
        conn.send(header_obj_size)
        conn.send(header_obj_bytes)
        # 读取客户选定的文件并逐行发送给客户端
        with open(file_path, 'rb') as f:
            for line in f:
                conn.send(line)
        print('end')
        break


def run(conn, addr):
    """进入新线程,开始接收数据"""

    # 接收客户端登录的用户名,筛选重复登录
    print('接收...')
    username_len = conn.recv(4)[0]
    username = conn.recv(username_len).decode('utf-8')
    print('登录的用户名<%s>' % username)
    if username not in login_user_lst:
        # 发送登录正常标识符
        conn.send('1'.encode('utf-8'))
        login_user_lst.append(username)
        print(login_user_lst)

    else:
        # 发送重复登录表示符
        conn.send("2".encode('utf-8'))

    while True:
        print('已连接:当前线程<%s>, 客户端端口<%s>' % (current_thread().name, addr[1]))

        choice = conn.recv(1)
        if not choice:
            collect(conn, q, login_user_lst, username)
            break
        print('choice<%s>' % choice)
        choice = choice.decode('utf-8')
        if choice in ['1', '2', '5']:
            if choice == '1':
                print('接收到1')
                receive(conn, username)  # 开始接收客户端上传的文件

            elif choice == '2':
                print('接收到2')
                transfer(conn, username)  # 开始向客户端发送文件

            elif choice == '5':
                collect(conn, q, login_user_lst, username)
                break  # 响应客户端的操作, 退出while循环并关闭conn连接


def server(ip, port):
    """创建服务器"""
    server = socket(AF_INET, SOCK_STREAM)
    server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server.bind((ip, port))
    server.listen(5)

    while True:
        # 生成套接字对象, 等待客户上门
        print("进入待连接状态>>> ")
        # 主线程停留于此,一直等待
        conn, addr = server.accept()
        print(addr)
        t = Thread(target=run, args=(conn, addr))
        try:
            q.put(t, block=False, timeout=0.5)
            # 阻塞会抛出queue.Full异常
        except queue.Full:
            # 抛出满队列的异常,并发送相应状态码
            conn.send('9'.encode('utf-8'))
        else:
            # 正常状态码
            conn.send('8'.encode('utf-8'))

        t.start()


def start_server():
    server(SERVER_IP, SERVER_PORT)

if __name__ == '__main__':
    start_server()


