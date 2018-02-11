# -*- coding: utf-8 -*-   @Time    : 18-1-25 下午7:29
# @Author  : QiHanFang    @Email   : qihanfang@foxmail.com
import subprocess
from os.path import join, getsize
import configparser

from conf.settings import *


def user_select_file(**kwargs):
    """用户选择服务端下载的文件并返回具体路径"""
    # # global file_path
    # file_path = ''
    if kwargs.get('type') == 'get':
        while True:
            print('服务器文件目录'.center(20, '-'))
            ls_obj = subprocess.Popen(' ls %s' % SERVER_SHARE_DIR, shell=True, stdout=subprocess.PIPE
                                      , stderr=subprocess.PIPE, )
            print(ls_obj.stdout.read().decode('utf8'))  # 打印文件夹目录
            print(''.center(20, '-'))

            holder_name = input('选择文件夹(q.返回主界面)>>> ').strip()
            if holder_name in get_holders_names(SERVER_SHARE_DIR):  # 文件夹名称输入正确则进入文件夹内部
                ls_holder_obj = subprocess.Popen(r'ls %s' % join(SERVER_SHARE_DIR, holder_name),shell=True
                                              ,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout = ls_holder_obj.stdout.read().decode('utf8').strip()
                stderr = ls_holder_obj.stderr.read().decode('utf8')
                print(stdout+stderr)  # 打印文件目录
                print(''.center(20, '-'))
                while True:
                    file_name = input('选择文件(b.返回上一层)>>> ').strip()
                    if file_name in get_file_names(join(SERVER_SHARE_DIR, holder_name)):
                        file_path = join(SERVER_SHARE_DIR, holder_name, file_name)
                        print('选择后的file_path: ', file_path)
                        return file_path
                    elif file_name == 'b':
                        break

            elif holder_name == 'q':
                return CHOICE_FLAG

    elif kwargs.get('type') == 'push':
        print('\n'+'选择上传文件'.center(20, '-'))
        upload_dir = kwargs.get('dir', '')
        obj = subprocess.Popen('ls %s' % upload_dir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, )
        print(obj.stdout.read().decode('utf8')+'\n')
        while True:
            choice = input('选择文件(q.返回主界面)>>> ').strip()
            if choice == 'q':
                return CHOICE_FLAG
            if not choice: continue
            file = choice.strip()
            file_obj = subprocess.Popen(r'ls %s' % join(upload_dir, file), shell=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, )
            stdout = file_obj.stdout.read().decode('utf8')
            stderr = file_obj.stderr.read().decode('utf8')
            if stdout and not stderr:
                file_path = stdout
                break

        return file_path


def show_user_file_holder(**kwargs):
    """打印用户download和upload文件夹下文件列表以及占用容量百分比"""
    type = kwargs.get('type', '')
    file_path = kwargs.get('dir', '')
    allowed_storage = kwargs.get('allowed_storage', '')
    obj = subprocess.Popen('ls %s' % file_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(obj.stdout.read().decode('utf-8'))
    if type == 'download':
        present_storage = get_file_holder_size(file_path)
        if not present_storage:
            present_storage = 0
        print('-----已占用容量{:.2f}%------'.format(present_storage / allowed_storage * 100))

    elif type == 'upload':
        print(''.center(20, '-'))


def get_file_holder_size(dir_name):
    """获取当前文件夹下所有文件的大小之和,不包含文件夹"""
    size = 0
    for root, dirs, files in os.walk(dir_name):
        size += sum([getsize(join(root, name)) for name in files])
        if not size:
            size=0
        return size


def get_file_names(dir_path):
    """获取当前文件夹下的文件名称列表,用于判断输入的名称是否在当前文件夹下的文件名称"""
    for root, dirs, files in os.walk(dir_path):
        return files


def get_holders_names(dir_path):
    """获取当前文件夹下的文件夹名称列表,用于判断输入的名称是否在当前文件夹下的文件夹名称"""
    for root, dirs, files in os.walk(dir_path):
        return dirs


def upgrade_storage(**kwargs):
    """升级当前用户下载目录空间大小"""
    config = configparser.ConfigParser()
    config.read(CONF_DIR)
    username = kwargs.get('username', '')
    old_storage = kwargs.get('old_storage', '')
    while True:
        new_storage = input('新申请的下载存储空间>>> ').strip()
        if new_storage.isdigit():
            if int(new_storage)*1024*1024 > int(old_storage):
                config.set(username, 'storage', new_storage)
                with open(CONF_DIR, 'w') as f:
                    config.write(f)
                    print('------升级成功,下载空间为%sM------' % new_storage)
                    input()
                    break
            else:
                print('\033[1;35m 必须大于初始内存空间 \033[0m')
        else:
            print('\033[1;35m 空间大小必须为数字 \033[0m')






