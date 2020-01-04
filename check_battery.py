# -*- coding: utf-8 -*-
"""
@version: 1.0
@author: 姜勇平
@email: idealage@126.com
@license: Apache Licence
@file: check_battery
@time: 2019-10-09
@remark: 
"""

import os, re, time
from datetime import datetime


def my_print(tip, label=''):
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('{0} [{1}] => {2}'.format(time_str, label, tip))


# 电池信息类
class Battery:
    def __init__(self):
        self.power_info = ''
        self.get_info()

    def __get_number_value(self, pattern):
        ret = re.search(pattern, self.power_info).group(1)
        return int(ret)

    def __get_string_value(self, pattern):
        return re.search(pattern, self.power_info).group().split(":")[1].strip()

    def get_info(self):
        self.power_info = os.popen("system_profiler SPPowerDataType").read()

    def max_capacity(self):
        return self.__get_number_value(r'Full Charge Capacity.*?(\d+)')

    def current_capacity(self):
        return self.__get_number_value(r'Charge Remaining.*?(\d+)')

    def cycle_count(self):
        return self.__get_number_value(r'Cycle Count.*?(\d+)')

    @staticmethod
    def design_capacity():
        info = os.popen('ioreg -l -w0 | grep DesignCapacity').read()
        return int(info.split("=")[1].strip())

    def percentage(self):
        return int(self.current_capacity()/self.max_capacity() * 100)

    def battery_health(self):
        return int(self.max_capacity() / self.design_capacity() * 100)

    def battery_condition(self):
        return self.__get_string_value(r'Condition.*')

    def is_charging(self):
        status = self.__get_string_value(r'Charging.*')
        if status == 'No':
            return False
        else:
            return True


# main start
if __name__ == '__main__':
    bat = Battery()
    def_remind_spec = 180       # 提醒间隔：秒
    def_power_offset = 4        # 电量偏移，获取到的值和系统任务栏显示的有差距
    def_min_percentage = 60     # 低水位值
    def_max_percentage = 90     # 高水位值
    cmd_base = 'osascript -e \'display notification "{0}" with title "JadeStar-电源管理-{1}"\''
    last_times = 0

    while True:
        time.sleep(30)
        bat.get_info()
        is_charging = bat.is_charging()
        cur_percentage = bat.percentage() + def_power_offset
        my_print('当前电量：{0}%，电源状态：{1}'.format(cur_percentage, '充电中' if is_charging else '未充电'))

        run_cmd = ''
        if cur_percentage <= def_min_percentage and not is_charging:
            run_cmd = cmd_base.format('您的电量已达到充电低水位值，请接通充电器！', '低电量告警')

        elif cur_percentage >= def_max_percentage and is_charging:
            run_cmd = cmd_base.format('您的电量已达到断电高水位值，请断开充电器！', '高电量告警')

        if run_cmd != '' and time.time() - last_times >= def_remind_spec:
            my_print('执行命令：{0}'.format(run_cmd))
            last_times = time.time()
            os.popen(run_cmd)

