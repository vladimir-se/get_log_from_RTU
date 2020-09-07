# Purpose:
The script downloads log files from RTU, archives them and sends an e-mail message about successful or unsuccessful download.

# Variable parameters:
- In archchecker.py file:
        - self.FTP_PATH="/pub/data/"
        - recipients=["to_1@email.ku", "tu_2@email.ku"]
        - server=smtplib.SMTP("192.168.1.1")
        - self.LOG_PATH=u"K:\путь к сетевой\папке"
        - self.LOG_PATH=u"/mnt/control"w

        cmd="sudo mount -t cifs "
        cmd += "//192.168.1.1/Share/путь\ к\ сетевой/папке "
        cmd += self.LOG_PATH+" "
        cmd += "-o username=my-username," 
        cmd += "domain=mydomain,"                   
        cmd += "password=MyPassword," 
        cmd += "uid=1005,gid=1005" 