<p align="center" background="black"><img src="un_top.svg" width="450"></p>

<p align="center">
</p>

# Python minter-guard service.

This is the "light" opensource version for everyone. OFC no guarantees, etc. Reduced part of our solution, used in production enviroment.

You can use it on any third-parity/rented servers. No need to store key on server for TX_OFF. It's possible to modify txgenerator to use it completely offline!

Created by <a href="https://www.u-node.net">https://www.u-node.net</a> co-founders Roman Matusevich (software programming) and Anatoly Ustinov (software architecture)

You can support our project by sending any Minter's coins to our wallet Mx6e0cd64694b1e143adaa7d4914080e748837aec9

Delegate to our 3% Minter masternode Mp02bc3c3f77d5ab9732ef9fc3801a6d72dc18f88328c14dc735648abfe551f50f

**Prerequiests and installation in example - <a href="https://centos.org/">Centos 7</a> minimal.**

Should run as systemd service under newly added user "minter-guard".

**Separate minter wallet (masternode owner) w/o output transactions is a must! Our team uses one wallet as a nodes owner and one as a reward address.**

## Preparation

### Install related packages

```
yum install -y https://centos7.iuscommunity.org/ius-release.rpm
yum -y install python36u-setuptools python36u python36u-devel python36u-libs python36u-pip python36u-tkinter python36u-tools gcc git
```

### Rest preparation

Execute step-by-step:

```
pip3.6 install --upgrade pip
useradd minter-guard
cd /home/minter-guard
pip3.6 install virtualenv
virtualenv appenv
chown -R minter-guard:minter-guard /home/minter-guard
su - minter-guard
source appenv/bin/activate
python -V
pip install git+https://github.com/U-node/minter-guard
pip install git+https://github.com/U-node/minter-sdk
exit
```

### Create startup script

Execute:

```
vi /usr/lib/systemd/system/minter-guard.service
```
Insert following:

```
[Unit]
Description=MinterGuard by https://www.unode.net team
After=network.target

[Service]
Type=simple
User=minter-guard
ExecStart=/home/minter-guard/appenv/bin/python /home/minter-guard/appenv/lib/python3.6/site-packages/minterguard/guard.py --config=/home/minter-guard/.config
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
Alias=minter-guard.service
```

### Create initial config

Execute:

```
vi /home/minter-guard/.config
```

Insert following (example):

```
[API]
API_URL = http://127.0.0.1:8841/ http://127.0.0.2:8841/

[NODE]
PUB_KEY = Mpd30a965324ffd01c3b61e898137bd6eacd69243b43512ab1dde1deca697f39ad
SET_OFF_TX = 
MISSED_BLOCKS = 3

[SERVICE]
LOG = /home/minter-guard/minter-guard.log
```
Note, that you **MUST** provide correct:
1. API nodes address.
2. PUB_KEY of your node.
3. MISSED_BLOCKS. This is trigger parameter to execute OFF_TX transaction. Note, that after execution of TX, your node will MISS _at least_ 2 next blocks.

API nodes **MUST** be synced to network **COMPLETELY**.
Provided txgenerator uses API node to get nonce for OFF_TX

### Generate OFF_TX

Execute:

```
/home/minter-guard/appenv/bin/python /home/minter-guard/appenv/lib/python3.6/site-packages/minterguard/txgenerator.py /home/minter-guard/.config off
```
You will need to paste seed phrase of masternode owner wallet.

You'll get the foloowing output (EXAMPLE):

```
Provide seed phrase (password like input): 
Public key: Mp02bc3c3f77d5ab9732ef9fc3801a6d72dc18f88328c14dc735648abfe551f50f
From address: Mxd5f1159a07cf913b08fbba443f3a8a2806ea87da
Set candidate OFF tx: f87c0101018a424950000000000000000ba2e1a002bc3c3f77d5ab9732ef9fc3801a6d72dc18f88328c14dc735648abfe551f50f808001b845f8431ba0cf958f8069b7f4a7605b70656c3e1765e40b8ee9183adbc3e715b032490ecc36a06ee455fa7b448006ca435b60eaa39ea5a0c3d8f3c676bcf83da4dd614ba3d9a9
```
You should doublecheck:
1. Public key
2. From address (masternode owner wallet)

### Update config with transaction

Execute:

```
vi /home/minter-guard/.config
```

Update following (example):

```
SET_OFF_TX = f87c0101018a424950000000000000000ba2e1a002bc3c3f77d5ab9732ef9fc3801a6d72dc18f88328c14dc735648abfe551f50f808001b845f8431ba0cf958f8069b7f4a7605b70656c3e1765e40b8ee9183adbc3e715b032490ecc36a06ee455fa7b448006ca435b60eaa39ea5a0c3d8f3c676bcf83da4dd614ba3d9a9
```

### Run service

Enable it:
```
chkconfig minter-guard on
```

Run it:
```
service minter-guard start
```

Check for errors:
```
tail -F /home/minter-guard/minter-guard.log
```
