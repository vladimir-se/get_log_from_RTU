# Purpose:
The script downloads log files from RTU, archives them and sends an e-mail message about successful or unsuccessful download.

# Variable parameters:
In archchecker.py file:
- self.FTP_PATH - path to logs on RTU;
- recipients - List of recipients of email alerts;
- server - Mail (SMTP) server address;
- self.LOG_PATH - Path to the directory where to save the archives of log files;
- Mount options for the remote directory (optional). See man mount.cifs.
``` bash
cmd="sudo mount -t cifs "
cmd += "//192.168.1.1/Share/путь\ к\ сетевой/папке "
cmd += self.LOG_PATH+" "
cmd += "-o username=my-username," 
cmd += "domain=mydomain,"                   
cmd += "password=MyPassword," 
cmd += "uid=1005,gid=1005"
```

For get-arch.py file is the same as in the file archchecker.py.

Syntax for ges_ip.txt file:
```bash
Object name or RTU name : ip-addresses separated by commas
```