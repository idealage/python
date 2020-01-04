# -*- coding: utf-8 -*-
"""
@version: 2.0
@author: 姜勇平
@email: idealage@126.com
@license: Apache Licence
@file: check_process.py
@time: 2018/10/20 01:38
@remark: 进程检测服务
"""

import psutil, logging
import threading, os, time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


#################################################################################################
# 初始化日志系统, 日志级别大小关系为：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
text_format = '%(asctime)s %(levelname)-7s => %(message)s'
logger = logging.getLogger("")  # 默认为“根”，可以是其它，例如："SLOW"
logger.setLevel(logging.DEBUG)  # 全局的日志级别

# 添加一个按时间滚动的日志文件(按天，每天1个，备份100个)
file_handler = TimedRotatingFileHandler(filename="./log/check_process.log", when="d", interval=1, backupCount=7)
file_handler.setFormatter(logging.Formatter(text_format))
file_handler.setLevel(logging.INFO)     # INFO 级别以上才记录
logger.addHandler(file_handler)

# 添加一个用于显示的接口
console = logging.StreamHandler()
console.setFormatter(logging.Formatter(text_format))
console.setLevel(logging.DEBUG)         # DEBUG 级别以上才显示
logger.addHandler(console)
#################################################################################################


# 打印时加上日期时间“2018-03-05 14:03:58,521 [label] =>”
# @tip      要打印的内容
# @label    标签，可为空
def my_print(tip, label=''):
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('{0} [{1}] => {2}'.format(time_str, label, tip))

# 功能：根据进程ID获取进程信息[name(), pid]
def get_process_by_id(pid):
    return psutil.Process(pid)

# 功能：根据进程名称获取进程信息[name(), pid]
def get_process_by_name(pname):
    for proc in psutil.process_iter():
        if proc.name().lower() == pname.lower():
            return proc

    return None


maxProcessNameLen = 5   # 进程名称最大长度
maxCheckCount = 0       # 用于保存各个进程中的最大检查次数

# 要监控的进程对象
class MonitorProcessObj(threading.Thread):

    # 类初始化
    # name_           进程名称
    # cmd_            要执行的命令
    # type_           检测类型，0=如果进程不存在则启动，1=每cond_time_秒重启进程, 2=规定时间重启
    # check_time_     检测时长，单位：秒
    # cond_time_      type_=2时的规定时间，单位：H24，例如“3”表示AM3点钟
    # rebootDelay_    杀掉进程后重启的延时
    def __init__(self, name_, cmd_, type_, check_time_, cond_time_ = [0], rebootDelay_ = 1):
        threading.Thread.__init__(self)
        self._proc_name = name_
        self._prog_cmd = cmd_
        self._proc_type = type_
        self._proc_check_time_ = check_time_
        self._proc_cond_time_ = cond_time_
        self._proc_rebootDelay_ = rebootDelay_

    # 线程的工作函数
    def run(self):
        lastHour = -1
        lastSecond = time.time()
        startTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prevTime = datetime.now()
        checkCount, restartCount = 0, 0
        logger.info('监控任务启动: ' + self._proc_name)
        
        global maxCheckCount
        while True:
            time.sleep(self._proc_check_time_)
            proc = get_process_by_name(self._proc_name)
            checkCount += 1
            maxCheckCount = max(maxCheckCount, checkCount)

            # 首先检测是否异常，只要异常就启动
            if proc is None:
                restartCount += 1;
                logger.warn('进程: {0} 异常, 重启次数:{1}, 启动 > {2}'.format(self._proc_name, restartCount, self._prog_cmd))
                os.startfile(self._prog_cmd)
                prevTime = datetime.now()
                continue

            # 每N秒重启进程模式
            if self._proc_type == 1:
                if time.time() - lastSecond >= self._proc_cond_time_[0]:
                    restartCount += 1;
                    lastSecond = time.time()
                    logger.warn('进程: {0} 满足重启条件, 重启次数: {1}, 启动 > {2}'.format(self._proc_name, restartCount, self._prog_cmd))
                    proc.terminate()
                    os.system("taskkill -f -im {0}".format(self._proc_name)) # 再用系统命令杀一次, linux下自行修改
                    time.sleep(self._proc_rebootDelay_)
                    os.startfile(self._prog_cmd)
                    prevTime = datetime.now()
                    continue

            # 规定时间模式
            elif self._proc_type == 2:
                curTime = datetime.now()
                if curTime.hour in self._proc_cond_time_:
                    if lastHour != curTime.hour:
                        restartCount += 1;
                        lastHour = curTime.hour
                        logger.warn('进程: {0} 满足重启条件, 重启次数: {1}, 启动 > {2}'.format(self._proc_name, restartCount, self._prog_cmd))
                        proc.terminate()
                        os.system("taskkill -f -im {0}".format(self._proc_name)) # 再用系统命令杀一次, linux下自行修改
                        time.sleep(self._proc_rebootDelay_)
                        os.startfile(self._prog_cmd)
                        prevTime = datetime.now()
                        continue
                else:
                    lastHour = -1
                     
            ccLen = str(len(str(maxCheckCount)))
            timeSpan = ((datetime.now() - prevTime).total_seconds()) / 60.0 / 60.0
            fmt = '进程: {0:' + str(maxProcessNameLen) + '} , 检测次数: {1:>' + ccLen + '}, 首启:{2}, 重启:{3}, 已正常运行:{4:.2f}h'
            logger.debug(fmt.format(self._proc_name, checkCount, startTime, prevTime.strftime('%Y-%m-%d %H:%M:%S'), timeSpan))

# main start
if __name__ == '__main__':

    os.system("title 服务监控")
    
    threads = [
        #MonitorProcessObj("GateFlowSend.exe",   r'D:\MyStudio\Code\GateFlowSend.bat', 0, 17),
        #MonitorProcessObj("WxMessageSend.exe",   r'D:\MyStudio\Code\WxMessageSend.bat', 1, 17, [30], 1),
        MonitorProcessObj("calc.exe",   r'calc.exe', 2, 5, [9]),
    ]

    for t in threads:
        time.sleep(1)
        maxProcessNameLen = max(maxProcessNameLen, len(t._proc_name))
        t.start()

    for t in threads:
        t.join()
