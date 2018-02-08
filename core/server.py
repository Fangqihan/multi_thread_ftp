# -*- coding: utf-8 -*-   @Time    : 18-2-8 下午5:11
# @Author  : QiHanFang    @Email   : qihanfang@foxmail.com

from socket import *
from threading import current_thread, Lock
from concurrent.futures import ThreadPoolExecutor
import json
import struct

from conf.settings import *
from utils.common_func import get_file_md5


def receive(conn):
    """接收客户端发过来的文件,并保存至服务器的设定的存储文件夹下"""
    print('当前线程<%s>'%current_thread().name)
    while True:
        header_size_obj = conn.recv(4)
        if header_size_obj.decode('utf-8') == CHOICE_FLAG:
            # 检查是否是返回主界面命令
            print('接收到服务端返回主界面')
            break

        if not header_size_obj: continue
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


def transfer(conn):
    """接收客户端选定的要下载的文件路径,并且将对应的文件传送给客户端"""
    print('当前线程<%s>'%current_thread().name)
    while True:
        file_path = conn.recv(8000).decode('utf-8').strip()  # 接收客户端选定的文件路径
        if file_path == CHOICE_FLAG:  # 检查是否是返回主界面命令
            print('接收到服务端返回主界面')
            break

        filename = file_path.split('/')[-1]
        try:
            file_size = os.path.getsize(file_path)
        except Exception as e:
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
        # mutex.aquire()
        conn.send(header_obj_size)
        conn.send(header_obj_bytes)
        # 读取客户选定的文件并逐行发送给客户端
        with open(file_path, 'rb') as f:
            for line in f:
                conn.send(line)
        break


def run(conn, addr, mutex):
    """进入新线程,开始接收数据"""
    print('已连接:当前线程<%s>, 客户端端口<%s>' %(current_thread().name, addr[1]))
    while True:
        try:
            print('========')
            choice = conn.recv(1).decode('utf-8')
            if not choice: break
            if choice in ['1', '2', '5']:
                if choice == '1':
                    print('接收到1')
                    receive(conn)  # 开始接收客户端上传的文件

                elif choice == '2':
                    print('接收到2')
                    print('线程<%s>开始下载文件' % current_thread().name)
                    mutex.acquire()
                    transfer(conn)  # 开始向客户端发送文件
                    mutex.release()

                elif choice == '5':
                    break  # 响应客户端的操作

        except ConnectionResetError:
            break
    # 若客户端那边的连接断开,那么这边的conn也应该断开
    conn.close()


def server(ip, port, pool):
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
        # 遇到客户端连接就创建新的线程
        pool.submit(run, conn, addr, mutex)
    
    server.close()


if __name__ == '__main__':
    # 创建线程池,最大同时运行线程数量为10
    mutex = Lock()
    pool = ThreadPoolExecutor(10)
    server(SERVER_IP, SERVER_PORT, pool)




