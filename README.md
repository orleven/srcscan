# SRC Scan

```
 ___________  _____   _____                 
/  ___| ___ \/  __ \ /  ___|                
\ `--.| |_/ /| /  \/ \ `--.  ___ __ _ _ __  
 `--. \    / | |      `--. \/ __/ _` | '_ \ 
/\__/ / |\ \ | \__/\ /\__/ / (_| (_| | | | |   version: 1.0
\____/\_| \_| \____/ \____/ \___\__,_|_| |_|   author: @orleven                                                                      
```

srcscan is a SRC assistant tool that periodically scans subdomains and requests WEB services on port 80/443 to check if it is available, and send result to you by e-mail.
Also srcscan can scan subdomain and scan url and scan vul for xray...

[![Python 3.7](https://img.shields.io/badge/python-3.7-yellow.svg)](https://www.python.org/)


### Install

```
pip3 install -r requirements.txt
```

### Usage

1. First, set basic, smtp config in srcscan.conf, and the srcscan.conf file is created the first time you run it.

```
[basic]
thread_num = 10
looptimer = 1209600 # two week
timeout = 5
max_retries = 3

[domain]
proxy = False
http_proxy = http://127.0.0.1:1080 # The proxy config for sub domian scan 
https_proxy = https://127.0.0.1:1080 # The proxy config for sub domian scan 

[crawlergo]
crawlergo_path = C:\Soft\MyTools\submon\tools\crawlergo_windows_amd64\crawlergo
chrome_path = C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
http_proxy = http://127.0.0.1:8080   # The proxy config for xray scan 
https_proxy = https://127.0.0.1:8080 # The proxy config for xray scan 
username = username # The proxy auth config for xray scan
password = password # The proxy auth config for xray scan


[smtp]
mail_host = smtp.163.com
mail_port = 465
mail_user = username
mail_pass = password
sender = username@163.com
receivers = username@qq.com,username@qq.com

[proxy]
proxy = False  # The setting of proxy
http_proxy = http://127.0.0.1:1080
https_proxy = https://127.0.0.1:1080

...
```

2 Scan 

2.1 Scan subdomain

```
py -3 srcscan.py -d example.com
py -3 srcscan.py -df file.text      # file path
py -3 srcscan.py -df domain         # dir path, and you can add domain.txt in ./domain/
py -3 srcscan.py -d example.com -ss # by nomal model
```

2.2 Scan subdomain and scan url and scan vul for xray 

2.2.1 Start running xray

```ssh
nohup ./xray_linux_amd64 webscan  --listen 0.0.0.0:8000  --html-output proxy.html & 
```

2.2.2 Start running srcscan.py.

```
py -3 srcscan.py -df domain -ss -vs # dir path, and you can add domain.txt in ./domain/
```

![show](https://raw.githubusercontent.com/orleven/srcscan/master/show/show.png)

3. And then, wait for e-mail of result.

![email](https://raw.githubusercontent.com/orleven/srcscan/master/show/email.png)

4. Also, you can see all result in srcscan.db.

![sqlitedb](https://raw.githubusercontent.com/orleven/srcscan/master/show/sqlitedb.png)

### Thacks

1. [recon](https://github.com/t0w4r/recon)