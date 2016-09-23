#!C:/Python27/python
# -*- coding: UTF-8 -*-   
# Twisted MMORPG   
# from twisted.internet.protocol import Factory   
# from twisted.protocols.basic import LineOnlyReceiver   
# from twisted.internet import reactor   
import random   
import string
from multiprocessing import Process
import subprocess
import sys,os
#加载模块
from  ping import ICMPProcess


import time
from SocketServer import TCPServer, BaseRequestHandler
from SocketServer import ThreadingTCPServer, StreamRequestHandler  
import socket
import traceback
#全局变量设置区域
processmodels={"ping":ICMPProcess}
#processmodels={}
HOST='192.168.0.117'
PORT=12345
BUFSIZ=1024
Unit =1000
def cur_file_dir():
    #获取脚本路径
    path = sys.path[0]
     #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
    if os.path.isdir(path):
        return path.decode('gbk')
    elif os.path.isfile(path):
        return os.path.dirname(path).decode('gbk')
current_path=cur_file_dir();
class MyBaseRequestHandlersr(StreamRequestHandler):
    """
    #从BaseRequestHandler继承，并重写handle方法
    """
    clients=[]
    process={'tcpdownload':[],"mailtest":[],"ping":[],"ftptest":[],"httptest":[],"video":[],"tcptest":[],"udptest":[]}
    def addClient(self):      
        self.clients.append(self)
        print "client arrive:",self.client_address
        print len(self.clients)
    def delClient(self):
        if self.isClient():
            self.clients.remove(self)
    def isClient(self):
        if self in self.clients:
            return True
        else:
            return False
    def sendAll(self,data):
        for client in  self.clients:
            client.wfile.write(data)
            client.wfile.flush()
            time.sleep(0.1)
    
    def handle(self):
        #循环监听（读取）来自客户端的数据
        try:
            self.wfile.write("welcome\r\n")
            #self.wfile.flush()
        except:
            traceback.print_exc()
        while True:
            #当客户端主动断开连接时，self.recv(1024)会抛出异常
            try:
                #一次读取1024字节,并去除两端的空白字符(包括空格,TAB,\r,\n)
                try:
                    data = self.rfile.readline().strip() 
                except socket.timeout:
                    continue
                print "data from client:",data
                if (not data) or data == "quit":
                    print u"关闭客户端"
                    self.wfile.write("ok")
                    #self.wfile.flush()
                    #print self.clients
                    self.request.close()
                    self.delClient()
                    break;
                #self.client_address是客户端的连接(host, port)的元组
                # print "receive from (%r):%r" % (self.client_address, data)
                if data.startswith('regist'):
                    self.addClient()
                    running_process=[process for process in self.process.keys() if self.process[process]]
                    if running_process:
                        print "process_alive,",running_process
                        self.wfile.write('process_alive '+' '.join(running_process))
                        self.wfile.flush()
                    else:
                        print "no no no "
                elif data.startswith('data'):
                    print "sendALL:",data
                    self.sendAll(data)
                elif data.startswith('command'):
                    print "command:",data
                    command=data.split(" ")
                    command_name=command[1]
                    command_obj=command[2]
                    command_args=command[3:]
                    if command_name=='lunch':
                        ret=self.lunchProcess(command_obj,command_args)
                        print "result:back,",ret
                        self.wfile.write(ret)
                else:
                    pass
                
                # self.request.sendall(data)
            except:
                traceback.print_exc()
                break
        self.delClient()
    def lunchProcess(self,command_process,args):
        if command_process not in self.process.keys():
            return ('-1',"no command_obj %s" % command_process)
        print args
        if args[0]=="start":
            if not self.process[command_process]:
                if args[1].find(",") == -1:
                    client_count=int(args[1])
                    repeat_times=client_count/Unit
                    lefttimes=client_count % Unit
                    if repeat_times==0 and lefttimes>0:
                        print "process:",processmodels[command_process]
                        print "args:",lefttimes
                        args[1]=lefttimes
                        p=Process(target=processmodels[command_process], args=tuple(args[1:]))    
                        self.process[command_process].append(p)
                        print self.process[command_process]
                else:
                    return "aaaaaaaa"
                #等待进程启动
                time.sleep(1)
                return "result 0 %s started\r\n" % command_process
                #启动服务
            else:
                return "result -1 %s has started\r\n" % command_process
                #已经开始
        elif args[0]=="stop":
            print u"停止服务:",command_process
            if not self.process[command_process]:
                # 错误，还没开始
                return "result -1 %s has not started\r\n" % command_process
            else:
                #开始停止
                for p in self.process[command_process]:
                    p.terminate()
                    p=None
                self.process[command_process]=[];
                return "result 0 %s stoped\r\n" % command_process
if __name__ == "__main__":
    #telnet 127.0.0.1 9999
    host = ""       #主机名，可以是ip,像localhost的主机名,或""
    port = 10087     #端口
    addr = (host, port)
    #购置TCPServer对象，
    server = ThreadingTCPServer(addr, MyBaseRequestHandlersr)
    #启动服务监听
    print u"TCP多线程服务器已经启动";
    server.serve_forever()
# print u"监听之前"        
# reactor.listenTCP(10086, StreamFactory())
# print u"服务器在10086监听"   
# reactor.run()