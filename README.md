代码参考: https://github.com/Fangqihan/multi_thread_ftp

## 项目启动:
1. 切换工作路径至bin目录下;
2. 启动`start_server.py`文件;
3. 随后启动`start_client.py`文件

#### 主要功能如下:
1. 用户认证;
2. 上传本地文件文件之服务器;
3. 从服务器目录中选定文件并下载;
4. 不支持多用户同时登录,重复登录的进程直接退出;
5. 服务端多线程并发服务, 且通过queue实现线程池;
6. 可以配置最大并发数:`setting.py/MAX_THREADS`;
启动须知:用户文件在conf.ini文件中可以查看,也可以新注册用户