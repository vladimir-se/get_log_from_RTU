#!/usr/bin/env python3
# coding: utf-8

from datetime import date, datetime, timedelta
from ftplib import FTP
from os import name, path, sep, system
from sys import exit

class MyClass():
    def __init__(self):
        self.syslog("Начало проверки")
        self.LOG_PATH=None
        self.LOGFILE=None
        self.FTP_PATH="/pub/data/"
        self.TD=str(date.today() - timedelta(1)) #вчерашняя дата
        self.checkArch()
        self.syslog("Окончание проверки")

    def mail(self):
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header

        # отправитель
        sender_name = Header("Система контроля ведения служебных архивов УСПД", "utf-8")
        sender_name.append("<from@email.ku>", "ascii")

        # получатели
        recipients=["to_1@email.ku", "tu_2@email.ku"]
        # тема письма
        subj="Анализ ведения служебных архивов на {0}".format(self.TD)
        # сообщение
        message=""
        # for ms in messages:
        #     message += '\n'+ms.rstrip()
        try:
            self.LOGFILE.seek(0)
            for i in self.LOGFILE.readlines():
                message += i.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
        except:
            self.syslog("Не могу открыть файл-отчет для отправки сообщения!")
            return(1)
        # формирование сообщения
        msg=MIMEText(message, "", "utf-8")
        msg['Subject']=subj
        msg['From']=sender_name
        msg['To']=', '.join(recipients)
        # отправка
        server=smtplib.SMTP("192.168.1.1")
        #server.set_debuglevel(1)
        try:
            server.sendmail(sender_name.__str__(), recipients, msg.as_string())
        except:
            self.syslog("Ошибка при отправке сообщения!")
        finally:
            server.quit()

    def syslog(self, msg):
        try:
            with open(path.splitext(__file__)[0]+".log", "a") as syslogfile:
                syslogfile.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S ")+msg+"\n")
            syslogfile.close()
        except:
            pass

    def mnt(self, mount):
        if name == "nt":
            self.LOG_PATH=u"K:\путь к сетевой\папке"
            if path.exists(self.LOG_PATH):
                return True
            else:
                self.syslog("Путь: "+self.LOG_PATH+" не доступен!")
                exit(1)
        if name == "posix":
            self.LOG_PATH=u"/mnt/control"
            if path.exists(self.LOG_PATH):
                if mount == 1:
                    if not (path.ismount(self.LOG_PATH)):
                        try:
                            cmd="sudo mount -t cifs "
                            cmd += "//192.168.1.1/Share/путь\ к\ сетевой/папке "
                            cmd += self.LOG_PATH+" "
                            cmd += "-o username=my-username," 
                            cmd += "domain=mydomain,"                   
                            cmd += "password=MyPassword," 
                            cmd += "uid=1005,gid=1005" 
                            return system(cmd) == 0
                            return True
                        except:
                            return False
                    else:
                            return True
                elif mount == 0:
                    try:
                        cmd="sudo umount "+self.LOG_PATH
                        system(cmd) == 0
                        return True
                    except:
                        self.syslog("Не удается освободить ресурс: "+self.LOG_PATH)
                        return False
            else:
                self.syslog("Путь: "+self.LOG_PATH+" не доступен!")
                exit(1)

    def getYearCatalog(self, year= '', uspd=''):
        try:
            ftp=FTP(uspd)
            ftp.login()

            # каталог года
            try:
                ftp.cwd(self.FTP_PATH+year)
                return (year, ftp)
            except:
                return (0, uspd)
        except:
            return (year, 0)

    def getMonthCatalog(self, year='', month='', ftp=isinstance):
        try:
            ftp.cwd(self.FTP_PATH+year+'/'+month)
            return (year, month, ftp)
        except:
            return (year, 0, ftp)

    def getDayCatalog(self, year='', month='', day='', ftp=isinstance):
        try:
            ftp.cwd(self.FTP_PATH+year+'/'+month+'/'+day)
            return(year, month, day)
        except:
            return (year, month, 0)

    def makeVAR(self):
        try:
            self.LOGFILE=open(self.LOG_PATH+sep+self.TD+".txt", "w+", encoding="cp1251", errors="ignore")
            with open(path.dirname(__file__)+sep+"ges_ip.txt", "r", encoding="cp1251") as f:
                ipfile=f.readlines()
            f.close()
            ipdict={}
            for i in ipfile:
                ipdict[i.split(':')[0]]=i.split(':')[1][:-1]
            return ipdict
        except:
            self.syslog("Нет доступа к файлу-отчету!")
            exit(1)

    def checkArch(self):
        self.mnt(1)
        archive=[]
        noarchive=[]
        ipdict=self.makeVAR()
        for ges,ip_adresses in sorted(ipdict.items()):
            for ip in ip_adresses.split(','):
                try:
                    chk=self.getYearCatalog(self.TD[:4], ip)
                    if(chk[1] == 0):
                        raise Exception

                    chk=self.getMonthCatalog(chk[0], self.TD[5:7], chk[1])
                    if(chk[1] == 0):
                        raise Exception

                    chk=self.getDayCatalog(chk[0], chk[1], self.TD[8:], chk[2])
                    if(chk[2] == 0):
                        raise Exception

                    archive.append("{0} : {1} \n".format(ges.encode('cp1251').decode('utf-8'), ip))
                except:
                    noarchive.append("{0} : {1} \n".format(ges.encode('cp1251').decode('utf-8'), ip))

        self.LOGFILE.write("Архивы ведутся:\n__________________________________\n")
        for i in archive:
            self.LOGFILE.write(i)
        self.LOGFILE.write("\nАрхивы не ведутся:\n_______________________________\n")
        for i in noarchive:
            self.LOGFILE.write(i)

        self.mail()
        self.LOGFILE.close()
        self.mnt(0)

def main():
    my=MyClass()

if __name__ == "__main__":
    main()
