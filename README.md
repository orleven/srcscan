# SubMon

```
        _____         _     ___  ___
       /  ___|       | |    |  \/  |
       \ `--.  _   _ | |__  | .  . |  ___   _ __
        `--. \| | | || '_ \ | |\/| | / _ \ | '_ \
       /\__/ /| |_| || |_) || |  | || (_) || | | |  version: 1.0
       \____/  \__,_||_.__/ \_|  |_/ \___/ |_| |_|  author: @orleven

```

Submon is a SRC assistant tool that periodically scans subdomains and requests WEB services on port 80/443 to check if it is available, and send result to you by e-mail.

[![Python 3.5](https://img.shields.io/badge/python-3.5-yellow.svg)](https://www.python.org/)


### Install

```
pip3 install -r requirements.txt
```

### Usage

1. First, set basic, smtp config in submon.conf, and the submon.conf file is created the first time you run it.

```
[basic]
thread_num = 100    # Just for web status requests threads, not include subdomain scan.
looptimer = 43200   # Scan subdomain every 43200 seconds.
...

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

[google_api]
developer_key = developer_key   # Your developer key
search_enging = search_enging   # Your search enging
```

2. Scan subdomian,
```
py -3 submon.py -d example.com
py -3 submon.py -f file.text      # file path
py -3 submon.py -f domain         # dir path, and you can add domain.txt in ./domain/
py -3 submon.py -d example.com -n # by nomal model
```

![show](https://raw.githubusercontent.com/orleven/submon/master/show/show.png)

3. And then, wait for e-mail of result.

![email](https://raw.githubusercontent.com/orleven/submon/master/show/email.png)

4. Also, you can see all result in submon.db.

![sqlitedb](https://raw.githubusercontent.com/orleven/submon/master/show/sqlitedb.png)

### Thacks

1. [recon](https://github.com/t0w4r/recon)