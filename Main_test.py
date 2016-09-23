#encoding=utf-8
import sys,os
import re
import time, qt4reactor
import socket
qt4reactor.install()
from PyQt4 import QtCore, QtGui
from Form_Main import Ui_MainWindow
from configobj import ConfigObj
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.internet import reactor
from sys import stdout
from log import LOG
import subprocess
import socket
# 全局
preg_ip = re.compile("^((?:(2[0-4]\d)|(25[0-5])|([01]?\d\d?))\.){3}(?:(2[0-4]\d)|(255[0-5])|([01]?\d\d?))$")
def check_net(server,timeout=0.5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        ret=sock.connect(server)
        sock.send("quit\r\n")
        print "check_net:",sock.recv(1024)
        sock.close()
        return 1
    except:
        return 0
#获取脚本文件的当前路径
def cur_file_dir():
     #获取脚本路径
     path = sys.path[0]
     #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
     if os.path.isdir(path):
         return path.decode('gbk')
     elif os.path.isfile(path):
         return os.path.dirname(path).decode('gbk')
class Echo(Protocol):
  def __init__(self,factory):
    self.factory=factory
  def dataReceived(self, data):
    if data.startswith('welcome'):
        self.transport.getHandle().sendall("regist\r\n")
        self.factory.Connected()
        print "regist"
    elif data.startswith('data'):
        data_list=data.split(' ')
        data_type=data_list[1]
        if data_type == "ping":
            data_value = data_list[2:]
            print "ping_recv_values:%s"%data_value
            self.factory.setPing(data_value)
    elif data.startswith('result'):
        print "lunch result:",data
        self.factory.setLunchResult(data)
    elif data.startswith('process_alive'):
        print "process_alive"
        self.factory.setProcessAlive(data.strip())
class EchoClientFactory(ReconnectingClientFactory):
    def __init__(self,window):
        self.win=window
    def startedConnecting(self, connector):
        print 'Started to connect.'
    def setLunchResult(self,data):
        self.win.setLunchResult(data)
    def setProcessAlive(self,data):
        self.win.setProcessAlive(data)
    def setPing(self,data):
        self.win.setPing(data)
    def Connected(self):
        self.win.Connected()
    def buildProtocol(self, addr):
        print 'Connected.'
        print 'Resetting reconnection delay'
        self.resetDelay()
        return Echo(self)
    def clientConnectionLost(self, connector, reason):
        print 'Lost connection. Reason:', reason
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        ReconnectingClientFactory.clientConnectionFailed(self, connector,reason)
class MainWindow(QtGui.QMainWindow):
    def __init__(self):
       QtGui.QMainWindow.__init__(self)
       self.ui=Ui_MainWindow()
       self.ui.setupUi(self)
       self.main_path=cur_file_dir()
       self.config_path=os.path.join(self.main_path,"config.ini")
       self.config = ConfigObj(self.config_path,encoding='UTF8')
       self.load_save()
       self.ui.setting_connect.clicked.connect(self.connectServer)
       # self.ui.run_tcp.clicked.connect(self.start_tcp)
       # self.ui.run_udp.clicked.connect(self.start_udp)
       # self.ui.run_mail.clicked.connect(self.start_mail)
       self.ui.run_ping.clicked.connect(self.start_ping)
       # self.ui.run_ftp.clicked.connect(self.start_ftp)
       # self.ui.run_http.clicked.connect(self.start_http)
       # self.ui.run_video.clicked.connect(self.start_video)
       # self.ui.setting_view_log.clicked.connect(self.view_log)
       self.connection=None
       self.workprocess=None
       workdir=os.path.join(os.path.dirname(self.main_path),"factory_2.py")
       appname="python %s" % workdir
       self.workprocess=subprocess.Popen(appname,creationflags=subprocess.CREATE_NEW_CONSOLE)
       #控件跟踪
       self.lunchctrl={"tcptest":self.ui.run_tcp,"mailtest":self.ui.run_mail,"ping":self.ui.run_ping,"ftptest":self.ui.run_ftp,"httptest":self.ui.run_http,
       "video":self.ui.run_video,"udptest":self.ui.run_udp,
       }
       #控件状态
       self.lunchstate={"tcpdownload":False,'mailtest':False,"ping":False,"ftptest":False,"httptest":False,"video":False,"tcptest":False,"udptest":False}
       self.log=None
    def Connected(self):
        print "connecte to Ser"
    def load_save(self):
        if self.config['server'] and self.config['server']['ip']:
            self.ui.setting_server.setText(self.config['server']['ip'])
            #print preg_ip.match(unicode(self.config['server']['ip']))
    def start_ping(self):
        dut_ip=self.ui.set_ping_ip.text()
        if not self.connection:
            QtGui.QMessageBox.critical(self,u"错误提示",u"请先连接Factory服务器")
            return
        action="start"
        print "lunchstate:",self.lunchstate['ping']
        if self.lunchstate['ping']:
            action="stop"
        else:
            action="start"
        self.connection.transport.getHandle().sendall("command lunch ping %s 1 %s \r\n" % (action,dut_ip))
    def setPing(self,data_value):
        self.ui.ping_time_avg.setText(unicode(data_value[2]))
        self.ui.ping_time_min.setText(unicode(data_value[1]))
        self.ui.ping_time_max.setText(unicode(data_value[0]))    
    def connectServer(self):
        server_addr=unicode(self.ui.setting_server.text())
        # 检查IP地址合法
        if not preg_ip.match(server_addr):
            QtGui.QMessageBox.critical(self,u"错误提示",u"服务器地址IP地址格式不对!")  
            return
        server_ip=self.config['server']['ip']
        if not check_net((server_addr,10087)):
            QtGui.QMessageBox.critical(self,u"错误提示",u"服务器连接不上，请检查连接!")  
            return
        if server_addr != server_ip:
            server_ip=server_addr
            self.config['server']['ip']=server_ip
            self.config.write()
        if not self.connection:
            self.connection=reactor.connectTCP(server_ip,10087,EchoClientFactory(self))
    def setLunchResult(self,data):
        # result 0 %s  started
        print "data:",data
        data=data.split(" ")
        result=data[1]
        ctrlobj=self.lunchctrl[data[2]]
        action=data[3].strip()
        if result=="-1":
            errormessage=" ".join(data[2:])
            QtGui.QMessageBox.critical(self,u"错误提示",unicode(errormessage))
        else:
            if action=="started":
                self.lunchstate[data[2]]=True
                ctrlobj.setText(u"停止")
                pass
            elif action=="stoped":
                self.lunchstate[data[2]]=False
                ctrlobj.setText(u"启动")
            else:
                pass
    def setProcessAlive(self,data):
        data=data.split(' ')
        if len(data)==1:
            return
        process_names=data[1:]
        self.lunchstate.update(dict.fromkeys(process_names,True))
        for process_name in process_names:
            ctrlobj=self.lunchctrl[process_name]
            ctrlobj.setText(u"停止")
app=QtGui.QApplication(sys.argv)  
main=MainWindow()  
main.show()  
app.exec_()
 
 
 
 # log=LOG()
# log.init_xls()
# log.init_width("ftp",[16,16,16,16])
# log.init_title("ftp",(u"客户端数量","",u"开始时间","",),0);
# log.init_title("ftp",(u"时间",u"上传速率",	u"下载速率",u"上传失败个数",u"下载失败个数"),1);		
# log.init_title("mail",(u"客户端数量","",u"开始时间","",),0);
# log.init_title("mail",(u"时间",u"发送时间",	u"接收时间",u"发送失败个数",u"接收失败个数"),1);
# log.init_title("http",(u"客户端数量","",u"开始时间","",),0);
# log.init_title("http",(u"时间",u"接收时间",	u"失败个数"),1);
# log.init_title("tcp",(u"客户端数量","",u"并发数","",u"开始时间"),0);
# log.init_title("tcp",(u"时间",u"延迟",	u"失败个数"),1);
# log.init_title("udp",(u"客户端数量","",u"并发数","",u"开始时间"),0);
# log.init_title("udp",(u"时间",u"延迟",	u"失败个数"),1);
# log.init_title("ping",(u"开始时间","",u"最大延时",""),0);
# log.init_title("ping",(u"时间",u"延迟"),1);
# log.save()
       