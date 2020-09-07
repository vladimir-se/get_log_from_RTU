#!/usr/bin/env python3
# coding: utf-8

from time import sleep
from datetime import datetime, timedelta
from threading import Thread
import queue
import os
import ftplib
import sys
import zipfile
import shutil
import subprocess

# формирование списка адресов УСПД по станционно
def buildDict():
    ges_file_path = os.path.dirname(os.path.realpath(__file__))+os.sep+"ges_ip.txt"
    station_dict = {}
    with open(ges_file_path, "r") as f:
        for line in f:
            if line[0] != '#':
                l = line.rstrip().split(':')
                station_dict[l[0]] = l[1].split(',')
        f.close()
    return(station_dict)

def syslog(msg):
    try:
        with open(os.path.splitext(os.path.realpath(__file__))[0]+".log", "a") as syslogfile:
            syslogfile.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S ")+msg+"\n")
        syslogfile.close()
    except:
        pass

# отправка оповещений
def mail(message, log_file=0, rtenergo=0):
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header
    # отправитель
    sender_name = Header("Система загрузки служебных архивов УСПД", "utf-8")
    sender_name.append("<from@email.ku>", "ascii")
    if rtenergo == 0:
        # получатели
        recipients=["to_1@email.ku", "tu_2@email.ku"]
    else:
        recipients="else_to@email.ku"
    # тема письма
    subj="Произведена выгрузка служебных архивов"
    # сообщение
    message=message+'\n'
    # for ms in messages:
    #     message += '\n'+ms.rstrip()
    if rtenergo == 0:
        try:
            with open(log_file, 'r') as logfile:
                for line in logfile.readlines():
                    message += line
        except:
            syslog("Не могу открыть файл-отчет для отправки сообщения!")
            return(1)
    # формирование сообщения
    msg=MIMEText(message, "", "utf-8")
    msg['Subject']=subj
    msg['From']=sender_name
    if rtenergo == 0:
        msg['To']=', '.join(recipients)
    else:
        msg['To']=recipients
    # отправка
    server=smtplib.SMTP("192.168.1.1")
    # server.set_debuglevel(1)
    try:
        server.sendmail(sender_name.__str__(), recipients, msg.as_string())
        syslog("Сообщение успешно отправлено по следующим адресам: {0}".format(recipients))
    except:
        syslog("Ошибка при отправке сообщения!")
    finally:
        server.quit()

def mnt(mount=1, local_mount_point="/mnt/local_mount_point", remote_mount_point="//192.168.1.1/mnt/remote_local_point"):
    if mount == 1:
        if not os.path.exists(local_mount_point):
            syslog("Отсутствует локальная точка монтирования!")
            sys.exit(1)
        if not (os.path.ismount(local_mount_point)):
            try:
                cmd="sudo mount -t cifs "
                cmd += remote_mount_point+" "
                cmd += local_mount_point+" "
                cmd += "-o username=my-username,"
                cmd += "domain=mydomain,"                   
                cmd += "password=MyPassword,"
                cmd += "uid=1005,gid=1005"
                os.system(cmd) == 0
                return True
            except:
                syslog("Не удается смонтировать удаленный ресурс: {0}".format(remote_mount_point))
                return False
        else:
                return True
    elif mount == 0:
        try:
            cmd = "sudo umount "+local_mount_point
            os.system(cmd) == 0
            return True
        except:
            syslog("Не удается освободить ресурс: {0}".format(local_mount_point))
            return False

def move(source, destination):
    try:
        shutil.move(os.path.dirname(os.path.realpath(__file__))+os.sep+source, destination)
        return True
    except Exception as e:
        syslog("Ошибка при перемещении архивов: {0}".format(e))
        return False

class Worker(Thread):
    def __init__(self, queue, thread_num, getfiles_date):
        super(Worker, self).__init__()
        self.setDaemon = True
        self._queue = queue
        self.getfiles_date = getfiles_date.split('-')
        self.remote_path = "/pub/data/"+self.getfiles_date[0]+"/"+self.getfiles_date[1]+"/"+self.getfiles_date[2]+"/"
        self.save_arch_path = os.path.dirname(os.path.realpath(__file__))
        self.thread_num = thread_num
        self.createArchLocalDir(self.save_arch_path)
        # очистка старых логов

    # создание локального дерева каталогов
    # для хранения архивов
    def createArchLocalDir(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                self.logger("Не могу создать каталог: {0}".format(path))
    
    # процедура журналирования
    def logger(self, message):
        try:  
            f = open(os.path.splitext(os.path.realpath(__file__))[0]+".log", "a")
            f.write(message+'\n')
            f.close()
        except:
            return(1)

    # архивация загруженных файлов
    def archivator(self, dir):
        arch_catalog = self.save_arch_path+os.sep+'-'.join(self.getfiles_date)
        if not os.path.exists(arch_catalog):
            try:
                os.makedirs(arch_catalog)
            except Exception as e:
                self.logger("Ошибка создания каталога для переноса архивов: {0}".format(e))
                return False
        try:
            rootdir = os.path.relpath(self.save_arch_path+os.sep+dir)
            if os.path.isdir(rootdir):
                zipf = zipfile.ZipFile(arch_catalog+os.sep+dir+".zip", 'w', zipfile.ZIP_DEFLATED)
                for root, dir, files in os.walk(rootdir):
                    for file in files:
                        zipf.write(os.path.join(root, file))
                zipf.close()
                shutil.rmtree(rootdir)
            return True
        except FileNotFoundError:
            return False

    # процедура загрузки архивов
    def run(self):
        while True:
            try:  
                ges, ip = self._queue.get(False).split(':')
            except queue.Empty:
                break
            else:
                # полный путь для локального хранения архивов (для каждой станции отдельно)
                path_to_local_arch_storage_for_ges = self.save_arch_path+os.sep+ip+os.sep+self.getfiles_date[0]+os.sep+self.getfiles_date[1]+os.sep+self.getfiles_date[2]
                #self.logger("{0} начало загрузки архивов {1}.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ges))
                # инициализация подключения к УСПД
                try:
                    ftp = ftplib.FTP(host=ip, timeout=5)
                    ftp.set_pasv(True)
                    ftp.login()
                except ftplib.all_errors as e:
                    self.logger("{0} Ошибка подключения к ftp {1} ({2}): {3}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ges, ip, e))
                    # ftp.close()
                    self._queue.task_done()
                else:
                    # определение ведения архивов
                    try:
                        ftp.cwd(self.remote_path)
                    except ftplib.all_errors as e:
                        self.logger("{0} Архивы не ведутся на: {1} ({2})".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ges, ip))
                        ftp.close()
                        self._queue.task_done()
                    else:
                        # получение списка файлов архивов
                        remote_files = ftp.nlst()
                        # создание локального дерева каталогов
                        self.createArchLocalDir(path_to_local_arch_storage_for_ges)
                        # загрузка файлов
                        for rfile in remote_files:
                            local_file = path_to_local_arch_storage_for_ges+os.sep+rfile
                            flag = 3
                            if flag > 0:
                                with open(local_file, 'wb') as loc_file:
                                    try:
                                        # непосредственная загрузка файлов
                                        ftp.retrbinary('RETR ' + rfile, loc_file.write, 1024)
                                    except ftplib.all_errors as e: # повторное переподключение к УСПД при обрыве связи
                                        flag = flag-1
                                        sleep(30)
                                        try:
                                            ftp.set_pasv(True)
                                            ftp.connect()
                                            ftp.login()
                                            ftp.cwd(self.remote_path)
                                        except:
                                            pass
                                    finally:
                                        loc_file.close()
                            else:
                                self.logger("{0} Ошибка загрузки файлов с {1} ({2}). Проблемы с каналами связи.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ges, ip))
                                ftp.close()
                                self._queue.task_done()
                        # если загрузка всех файлов с УСПД прошла успешно
                        self.logger("{0} загрузка архивов успешно завершена {1} ({2}).".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ges, ip))
                        ftp.close()
                        if not self.archivator(ip):
                            self.logger("{0} Ошибка создания архива {1}.zip".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip))
                        self._queue.task_done()

def main():
    try:
        os.remove(os.path.splitext(os.path.realpath(__file__))[0]+".log")
    except:
        pass
    gesDict = buildDict()
    getfiles_date = datetime.date(datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d")

    # создание очереди с неограниченным количеством элементов
    ges_queue = queue.Queue()
     # заполнение очереди
    for ges in gesDict:
        for ip in gesDict[ges]:
            ges_queue.put(ges+':'+ip)
    # создание и запуск потоков(5)
    for i in range(1, 6):
        w = Worker(ges_queue, i, getfiles_date)
        sleep(3)
        w.start()
    # ожидание завершения задания по каждому элементу очереди
    ges_queue.join()

    if ges_queue.empty():
        if mnt():
            if move(getfiles_date, "/home/mnt/local_mount_point"):
                mail("Служебные архивы УСПД готовы для анализа.", os.path.splitext(os.path.realpath(__file__))[0]+".log")
                mail("Служебные архивы УСПД готовы для анализа.\nПросьба забрать их с ресурса.\n\nP.S. Письмо отправлено автоматически, отвечать на него не требуется.", rtenergo=1)
            mnt(0)

if __name__ == "__main__":
    main()
