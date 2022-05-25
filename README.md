# PirateAudio_Volumio

PIMORONI製のPirate Audioを使用し、RasberryPiで動作のVolumioを操作とLCDに表示。
<image>

# 設定
## 日本語フォント
$ sudo apt install fonts-ipgexfont


## Python
$ sudo apt install python-rpi.gpio python-spidev python-pip python-pil python-numpy

## LCD
$ sudo pip install st7789

## スクリプト追記
$ sudo vim /etc/rc.local  
gpio -g mode 16 up  
gpio -g mode 20 up

/user/bin/python /home/volumio/PirateAudio/PirateAudio0503.py &

exit 0

# 操作
