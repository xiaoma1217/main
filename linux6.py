import os
import re

banner = """\033[1;34m
      (_)                            
__  ___  __ _  ___  _ __ ___   __ _ 
\ \/ / |/ _` |/ _ \| '_ ` _ \ / _` |
 >  <| | (_| | (_) | | | | | | (_| |
/_/\_\_|\__,_|\___/|_| |_| |_|\__,_|

    linux自动化巡检工具                             Version：1.0
                                                  Author：dqq\033[0m
"""
print(banner)


def get_cpu():
    global last_worktime, last_idletime
    f = open("/proc/stat", "r")
    line = ""
    while not "cpu " in line: line = f.readline()
    f.close()
    spl = line.split(" ")
    worktime = int(spl[2]) + int(spl[3]) + int(spl[4])
    idletime = int(spl[5])
    dworktime = (worktime - last_worktime)
    didletime = (idletime - last_idletime)
    rate = float(dworktime) / (didletime + dworktime)
    last_worktime = worktime
    last_idletime = idletime
    if (last_worktime == 0): return 0
    return rate


def get_mem_usage_percent():
    try:
        f = open('/proc/meminfo', 'r')
        for line in f:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemFree:'):
                mem_free = int(line.split()[1])
            elif line.startswith('Buffers:'):
                mem_buffer = int(line.split()[1])
            elif line.startswith('Cached:'):
                mem_cache = int(line.split()[1])
            elif line.startswith('SwapTotal:'):
                vmem_total = int(line.split()[1])
            elif line.startswith('SwapFree:'):
                vmem_free = int(line.split()[1])
            else:
                continue
        f.close()
    except:
        return None
    physical_percent = usage_percent(mem_total - (mem_free + mem_buffer + mem_cache), mem_total)
    virtual_percent = 0
    if vmem_total > 0:
        virtual_percent = usage_percent((vmem_total - vmem_free), vmem_total)
    return physical_percent, virtual_percent


def usage_percent(use, total):
    try:
        ret = (float(use) / total) * 100
    except ZeroDivisionError:
        raise Exception("ERROR - zero division error")
    return ret


def ostype():
    a = os.popen("lsb_release -a").read()
    sysnum = int(re.findall(" (\d+?)\.", a, re.S)[0])
    system = ''
    try:
        system = re.search('CentOS', a).group()
    except:
        pass
    try:
        system = re.search('Ubuntu', a).group()
    except:
        pass
    try:
        system = re.search('openSUSE', a).group()
    except:
        pass
    try:
        system = re.search('Red Hat', a).group()
    except:
        pass
    try:
        system = re.search('Kali', a).group()
    except:
        pass
    return system, sysnum


def account_check():
    account_list = []
    cmd = os.popen("cat /etc/shadow").read()
    user_list = re.split(r'\n', cmd)
    for i in user_list:
        try:
            c = re.search(r'\*|!', i).group()
        except:
            try:
                ok_user = re.findall(r'(.+?):', i)[0]
                account_list.append(ok_user)
            except:
                pass
    anonymous_account = os.popen("awk -F: 'length($2)==0 {print $1}' /etc/shadow").read()
    account = '存在的账户：\n{0}\n空口令用户：\n{1}\n'.format(account_list, anonymous_account)
    return account


def process():

    process = os.popen("ps -ef").read()
    return process


def service(system, sysnum):
    service = ''
    if system == 'Ubuntu' or system == 'Debian':
        service = os.popen("service --status-all | grep +").read()
    elif system == 'openSUSE':
        service = os.popen("service --status-all | grep running").read()
    elif system == 'CentOS' or system == 'Red Hat':
        if sysnum < 7:
            service1 = os.popen("chkconfig --list |grep 2:启用").read()
            service2 = os.popen("chkconfig --list |grep 2:on").read()
            service = service1 + '\n' + service2
        else:
            service = os.popen("systemctl list-units --type=service --all |grep running").read()
    return service


def startup(system, sysnum):
    startup = ''
    if system == 'CentOS' or system == 'Red Hat':
        if sysnum < 7:
            startup = os.popen("cat /etc/rc.d/rc.local").read()
        else:
            startup = os.popen("systemctl list-unit-files | grep enabled").read()
    elif system == 'Ubuntu' or system == 'Debian':
        if sysnum < 14:
            startup1 = os.popen("chkconfig |grep on").read()
            startup2 = os.popen("chkconfig |grep 启用").read()
            startup = startup1 + startup2
        else:
            startup = os.popen("systemctl list-unit-files | grep enabled").read()
    elif system == 'openSUSE':
        startup1 = os.popen("chkconfig |grep on").read()
        startup2 = os.popen("chkconfig |grep 启用").read()
        startup = startup1 + startup2
    return startup


def timingtask():
    timingtask = []
    cmd = os.popen("cat /etc/shadow").read()
    user_list = re.split(r'\n', cmd)
    for i in user_list:
        try:
            c = re.search(r'\*|!', i).group()
        except:
            try:
                ok_user = re.findall(r'(.+?):', i)[0]
                task = os.popen("crontab -l -u " + ok_user).read()
                timingtask.append(task)
            except:
                pass
    return timingtask


def seclog_time():
    cmd = os.popen("cat /etc/logrotate.conf").read()
    try:
        seclog = ''
        cycle = re.findall(r'# rotate log files weekly\n(.+?)\n', cmd, re.S)[0]  # 周期
        num = re.findall(r'\d+', str(re.findall(r'# keep 4 weeks worth of backlogs\n(.+?)\n', cmd, re.S)))[0]  # 次数
        print('轮转周期：{0}\n轮转次数：{1}'.format(cycle, num))
        if cycle == 'weekly':
            if int(num) < 26:
                seclog = '日志存留不足180天'
            else:
                seclog = '日志存留时间符合要求'
        elif cycle == 'monthly':
            if int(num) < 6:
                seclog = '日志存留不足180天'
            else:
                seclog = '日志存留时间符合要求'
        elif cycle == 'quarterly':
            if int(num) < 2:
                seclog = '日志存留不足180天'
            else:
                seclog = '日志存留时间符合要求'
        return seclog
    except:
        seclog = '日志轮转配置读取出错'
        return seclog


def seclog_login(system):
    succeed = failed = ''
    if system == 'CentOS' or system == 'Red Hat':
        succeed = '\n成功登录：\n' + os.popen(
            "cat /var/log/secure*|awk '/Accepted/{print $(NF-3)}'|sort|uniq -c|awk '{print $2\"|次数=\"$1;}'").read()
        failed = '\n失败登录：\n' + os.popen(
            "cat /var/log/secure*|awk '/Failed/{print $(NF-3)}'|sort|uniq -c|awk '{print $2\"|次数=\"$1;}'").read()
    elif system == 'Ubuntu' or system == 'Debian':
        succeed = os.popen(
            "cat /var/log/auth.log|awk '/Accepted/{print $(NF-3)}'|sort|uniq -c|awk '{print $2\"|次数=\"$1;}'").read()
        failed = os.popen(
            "cat /var/log/auth.log|awk '/authentication failure/{print $(NF-1)}'|sort|uniq -c|awk '{print $2\"|次数=\"$1;}'").read()
        succeed = '\n成功登录：\n' + re.sub("rhost=\|次数=\d|ruser=\|次数=\d|rhost=", "", succeed)
        failed = '\n失败登录：\n' + re.sub("rhost=\|次数=\d|ruser=\|次数=\d|rhost=", "", failed)
    elif system == 'openSUSE':
        succeed = '\n成功登录：\n' + os.popen(
            "cat /var/log/messages|awk '/Accepted/{print $(NF-3)}'|sort|uniq -c|awk '{print $2\"|次数=\"$1;}'").read()
        failed = '\n失败登录：\n' + os.popen(
            "cat /var/log/messages|awk '/failure/{print $(NF)}'|sort|uniq -c|awk '{print $2\"|次数=\"$1;}'").read()
    return succeed, failed


def firewall(system, sysnum):
    firewall = ''
    if system == 'CentOS' or system == 'Red Hat':
        if sysnum < 7:
            firewall = os.popen("service iptables status").read()
        else:
            firewall = os.popen("systemctl status firewalld").read()
    elif system == 'Ubuntu' or system == 'Debian':
        firewall = os.popen("ufw status").read()
    elif system == 'openSUSE':
        firewall = os.popen("chkconfig -list | grep fire").read()
    return firewall


def se_linux():
    se = os.popen('sestatus -v').read()
    if se != re.findall('disabled', se):
        print('SElinux处于关闭状态')
    else:
        print('SElinux处于开启状态')
    return se


def wenjian():
    a = os.popen('rpm -Va |grep "^S"').read()

    return a


if __name__ == '__main__':
    num = """"\033[1;34m
                0.默认执行
                1.系统状态
                2.账户情况
                3.运行的进程
                4.开启的服务
                5.启动项
                6.定时任务
                7.登录日志
                8.防火墙状态
                9.校验文件完整性
                10.SElinux
                q|Q.退出
            \033[0m"""
    print('程序正在自检 请稍后。。。。。。')
    if os.popen("whoami").read() != 'root\n':
        print('请在root用户权限下运行...')
        exit()
    elif not os.popen('lsb_release -a').read():
        print('请安装lsb_release -a，\n yum install -y  redhat-lsb')
        exit()

    else:

        while True:
            print(num)
            user_num = input('请输入要检查的内容').strip()
            if user_num == '0':
                last_worktime = 0
                last_idletime = 0
                statvfs = os.statvfs('/')
                total_disk_space = statvfs.f_frsize * statvfs.f_blocks
                free_disk_space = statvfs.f_frsize * statvfs.f_bfree
                disk_usage = (total_disk_space - free_disk_space) * 100.0 / total_disk_space
                disk_usage = int(disk_usage)
                disk_tip = "硬盘空间使用率：" + str(disk_usage) + "%"
                mem_usage = get_mem_usage_percent()
                mem_usage = int(mem_usage[0])
                mem_tip = "物理内存使用率：" + str(mem_usage) + "%"
                cpu_usage = int(get_cpu() * 100)
                cpu_tip = "CPU使用率：" + str(cpu_usage) + "%"
                load_average = os.getloadavg()
                load_tip = "系统负载：" + str(load_average) + '\n判断:系统负载中三个数值中有一个超过3就是高'
                system = ostype()[0]
                sysnum = ostype()[1]
                print(f'系统版本{system}-{sysnum}')
                print('\n【系统状态】')
                print(disk_tip)
                print(mem_tip)
                print(cpu_tip)
                print(load_tip)
                print('【账户情况】')
                print(account_check())
                print('【运行的进程】\n')
                print(process())
                print('\n【开启的服务】\n')
                print(service(system, sysnum))
                print('\n【启动项】\n')
                print(startup(system, sysnum))
                print('\n【定时任务】\n')
                for timingtask in timingtask():
                    print(timingtask)
                print('\n【登录日志】\n')
                print('日志存留时间：')
                print(seclog_time())
                print(seclog_login(system)[0])
                print(seclog_login(system)[1])
                print('\n【校验文件完整性】\n')
                print(f'这个文件被修改请注意查看--{wenjian()}')
                print('\n【防火墙状态】：\n')
                print(firewall(system, sysnum))
                print('\n【SElinux状态】\n')
                print(se_linux())
                exit()
            elif user_num == '1':
                last_worktime = 0
                last_idletime = 0
                statvfs = os.statvfs('/')
                total_disk_space = statvfs.f_frsize * statvfs.f_blocks
                free_disk_space = statvfs.f_frsize * statvfs.f_bfree
                disk_usage = (total_disk_space - free_disk_space) * 100.0 / total_disk_space
                disk_usage = int(disk_usage)
                disk_tip = "硬盘空间使用率：" + str(disk_usage) + "%"
                mem_usage = get_mem_usage_percent()
                mem_usage = int(mem_usage[0])
                mem_tip = "物理内存使用率：" + str(mem_usage) + "%"
                cpu_usage = int(get_cpu() * 100)
                cpu_tip = "CPU使用率：" + str(cpu_usage) + "%"
                load_average = os.getloadavg()
                load_tip = "系统负载：" + str(load_average) + '\n判断:系统负载中三个数值中有一个超过3就是高'
                system = ostype()[0]
                sysnum = ostype()[1]
                print('【账户情况】\n')
                print(disk_tip)
                print(mem_tip)
                print(cpu_tip)
                print(load_tip)
                continue
            elif user_num == '2':
                print('【账户情况】')
                print(account_check())
                continue
            elif user_num == '3':
                print('【运行的进程】\n')
                print(process())
                continue
            elif user_num == '4':
                print('【开启的服务】\n')
                print(service(system, sysnum))
                continue
            elif user_num == '5':
                print('【启动项】\n')
                print(startup(system, sysnum))
                continue

            elif user_num == '6':
                print('【定时任务】\n')
                for timingtask in timingtask():
                    print(timingtask)
                continue
            elif user_num == '7':
                print('【登录日志】\n')
                print('日志存留时间：')
                print(seclog_time())
                print(seclog_login(system)[0])
                print(seclog_login(system)[1])
                continue
            elif user_num == '8':
                print('【防火墙状态】：\n')
                print(firewall(system, sysnum))
                continue
            elif user_num == '9':
                print('【校验文件完整性】')
                print(f'这个文件被修改请注意查看:\n{wenjian()}')
                continue
            elif user_num == '10':
                print('【SElinux状态】')
                print(se_linux())
                continue
            elif user_num == 'q' or user_num == 'Q':
                print('拜拜 剩下的靠你了 See you')
                exit()

            else:
                print('输入有误 请重新输入')
