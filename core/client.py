# -*- coding: utf-8 -*-   @Time    : 18-2-8 下午5:11
# @Author  : QiHanFang    @Email   : qihanfang@foxmail.com
from socket import *
from os.path import getsize
import json
import struct

from conf.settings import *
from core.user_operations import user_select_file, show_user_file_holder, get_file_holder_size, upgrade_storage
from utils.common_func import get_file_md5
from core.auth import login


def download(client, download_dir, allowed_storage):
    """从服务器的文件目录下选择文件下载至本地download目录下"""
    while True:
        file_path = user_select_file(type='get')  # 获取选定要下载的服务器文件的路径或其他
        if file_path == CHOICE_FLAG:  # 检查是否是返回主界面命令
            client.send(file_path.encode('utf8'))
            return
        file_path = file_path.strip()
        size = getsize(file_path)  # 判断本地download目录容量是否足够下载文件
        present_storage = get_file_holder_size(download_dir)
        if not present_storage: present_storage=0
        if present_storage + size > allowed_storage:
            print('\n'+'>>>\033[1;35m 下载失败,您的存储空间不足 \033[0m!')
            return
        client.send(file_path.encode('utf-8'))  # 向服务端发送选定的文件路径
        header_size_obj = client.recv(4)  # 接收header长度定长pack
        header_obj_size = struct.unpack('i', header_size_obj)[0]
        # 根据header长度取得文件的header信息
        header_obj_json = client.recv(header_obj_size).decode('utf8')
        header_obj_dict = json.loads(header_obj_json)
        filename = header_obj_dict.get('filename', '')
        total_size = header_obj_dict.get('size', '')
        old_md5 = header_obj_dict.get('md5', '')
        # 逐行接收服务端返回的文件
        recv_size = 0
        save_path = join(download_dir, filename)
        print(save_path)
        with open(save_path, 'wb') as f:
            while recv_size < total_size:
                rec1 = client.recv(8888)
                f.write(rec1)
                recv_size += len(rec1)
            print('\n'+'----下载进度:{:.2f}%-----'.format(recv_size / total_size * 100))
        # 源文件和下载后文件一致性检验
        new_md5 = get_file_md5(save_path)
        if new_md5 == old_md5:
            print('\n-----\033[1;35m 文件一致性匹配 \033[0m-----')
            input()
            break
        else:
            print('----\n\033[1;35m 服务端发送的文件与收到的文件不一致 \033[0m---')
        break


def upload(client, upload_dir):
    """从本地upload目录下选择文件上传至服务器"""

    while True:
        # 1.选定上传的文件并获取其存储路径
        file_path = user_select_file(type='push', dir=upload_dir)
        if file_path == CHOICE_FLAG:  # 判断是否返回主界面
            client.send(file_path.encode('utf8'))
            return
        file_path = file_path.strip()
        filename = file_path.split('/')[-1]
        file_size = os.path.getsize(file_path)
        # 2.制作文件的header信息
        header = {
            'filename': filename,
            'md5': get_file_md5(file_path),
            'size': file_size,
        }
        header_obj = json.dumps(header)  # 序列化成str类型
        header_obj_bytes = header_obj.encode('utf-8')
        # 3.将报头字节大小制作成定长字节串并发送给客户端
        header_size_obj = struct.pack('i', len(header_obj_bytes))

        client.send(header_size_obj)
        client.send(header_obj_bytes)
        # 6.读取客户选定的文件并逐行发送给客户端
        with open(file_path, 'rb') as f:
            for line in f:
                client.send(line)

        result_size = client.recv(4)[0]
        # 接收服务端返回信息
        result_bytes = client.recv(result_size)
        result_dic = json.loads(result_bytes.decode('utf-8'))
        file_check = result_dic.get('file_check', '')
        upload_status = result_dic.get('upload_status', '')
        print('\n'+str(file_check).center(20, '-'))
        print('-----完成进度:{:.2f}%------'.format(float(upload_status)*100))
        input()
        break


@login
def run_client(**kwargs):
    """启动客户端,在用户登录后从conf.ini文件中获取用户的相关信息"""''
    client = socket(AF_INET, SOCK_STREAM)
    client.connect((SERVER_IP, SERVER_PORT))
    download_dir = kwargs.get('download_dir', '')
    upload_dir = kwargs.get('upload_dir', '')
    allowed_storage = kwargs.get('allowed_storage', '')
    username = kwargs.get('username', '')
    # 向服务端发送当前进程登录的用户名
    struct_obj = struct.pack('i', len(username))
    client.send(struct_obj)
    client.send(username.encode('utf-8'))
    # 接收服务端返回的结果
    res = client.recv(1).decode('utf-8')

    if res == '1':
        print('登录成功'.center(20, '-'))

        while True:
            print('用户操作主界面'.center(20, '-'))
            choice = input('1.上传\n2.下载\n3.查看已下载文件\n4.查看待上传文件\n5.退出登录\n6.升级存储空间\n输入操作编号>>> ').strip()
            if choice in ['1', '2', '3', '4', '5', '6']:

                if choice == '1':
                    # 上传本地文件
                    client.send(choice.encode('utf-8'))  # 将选择信息反馈给服务器
                    upload(client, upload_dir)

                elif choice == '2':
                    # 下载服务器文件
                    client.send(choice.encode('utf-8'))
                    download(client, download_dir, allowed_storage)

                elif choice == '3':
                    print('用户已下载文件'.center(20, '-'))  # 查看用户的download目录文件
                    show_user_file_holder(type='download', dir=download_dir, allowed_storage=allowed_storage)
                    input()

                elif choice == '4':
                    print('用户待上传文件'.center(20, '-'))  # 查看用户的upload目录的可上传文件
                    show_user_file_holder(type='upload',dir=upload_dir)
                    input()

                elif choice == '5':
                    choice = input('确认退出(q)>>> ')
                    if choice == 'q' or choice == 'quit':  # 退出并关闭客户端与服务端
                        client.send('5'.encode('utf8'))
                        # login(run_client)()
                        break

                elif choice == '6':
                    upgrade_storage(username=username, old_storage=allowed_storage)

        client.close()
        exit('退出')

    elif res == '2':
        print('\033[1;35m目前不支持多用户登录  \033[0m')


if __name__ == '__main__':
    run_client()

















