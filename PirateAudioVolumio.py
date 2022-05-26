#!/usr/bin/env python3
# coding: utf_8
#
#　Pirate Audioでvolumioをコントロール
#　　４つのボタンのコントロール
#　　LCDに情報表示
#　　　2020/ 5/ 3
#      2022/ 5/25 1st release
#
import io
import sys
import signal
import RPi.GPIO as GPIO
import os
import requests
from PIL import Image
from PIL import ImageFilter
from PIL import ImageDraw
from PIL import ImageFont
import json
import time
import ST7789

#
#　GLOBAL
panelMode = 1			
scriptPath = os.path.dirname(os.path.abspath(__file__))

# Prameters
GAUSSIANBLUR =  5.0
SCROLL_WIDTH = 13

# Font
#LCD_FONT   = "/home/volumio/PirateAudio/volumio/IPA_font/ipagp.ttf"
LCD_FONT   = "fonts-japanese-gothic.ttf"
smallFontTitle    = ImageFont.truetype(LCD_FONT,25)
smallFontArtist   = ImageFont.truetype(LCD_FONT,18)
smallFontAlbum    = ImageFont.truetype(LCD_FONT,14)
regularFontTitle  = ImageFont.truetype(LCD_FONT,38)
regularFontArtist = ImageFont.truetype(LCD_FONT,30)
regularFontAlbum  = ImageFont.truetype(LCD_FONT,24)
pAlbumX  =   0
pAlbumY  =   4
pArtistY =   0
pArtistY =  50
pTitleX  =   0            
pTitleY  = 105


# GPIOボタン番号とvolumioコマンド定義
GPIO_BUTTONS  = [5, 6, 16, 20]
GPIO_COMMANDS = ['toggle', 'volume&volume=minus', 'mode', 'volume&volume=plus', 'prev', 'next']

#
# volumio 関係定数
#
VOLUMIO_URL  = "http://127.0.0.1:3000"
VOLUMIO_CMD  = VOLUMIO_URL + "/api/v1/commands/?cmd="
VOLUMIO_STAT = VOLUMIO_URL + "/api/v1/getstate"
#
# Volumioから属性の読み込み
#
def VolumioStatus():
    global curStatus

    statVolumio = requests.get(VOLUMIO_STAT)
    try:
        tmp = statVolumio.json()['albumart']
    except:
        tmp = ""

    if tmp.find('http') == -1:
        tmp = VOLUMIO_URL + tmp

    curStatus["albumArtUrl"] = tmp
       
    try:
        curStatus["status"] = " " if statVolumio.json()['status'] is None else statVolumio.json()['status']
    except:
        curStatus["status"] = " "
    try:
        curStatus["title"]  = " " if statVolumio.json()['title']  is None else statVolumio.json()['title']
    except:
        curStatus["title"]  = " "
    try:
        curStatus["artist"] = " " if statVolumio.json()['artist'] is None else statVolumio.json()['artist']
    except:
        curStatus["artist"] = " "
    try:
        curStatus["album"]  = " " if statVolumio.json()['album']  is None else statVolumio.json()['album']
    except:
        curStatus["album"]  = " "
    try:
        curStatus["volume"] = " " if statVolumio.json()['volume']  is None else statVolumio.json()['volume']
    except:
        curStatus["volume"] = " "
    try:
        curStatus["seek"] = " " if statVolumio.json()['seek']  is None else statVolumio.json()['seek']
    except:
        curStatus["seek"] = " "
    try:
        curStatus["duration"] = " " if statVolumio.json()['duration']  is None else statVolumio.json()['duration']
    except:
        curStatus["duration"] = " "

#
#　Volumioからアルバムアートの読み込み
#
def GetAlbumArt():
    global curStatus, imageAlbum, LCDw, LCDh

    imageAlbum = Image.open(io.BytesIO(requests.get(curStatus["albumArtUrl"]).content))	# アルバムアートの更新
    imageAlbum = imageAlbum.resize((LCDw,LCDh));
    imageAlbum = imageAlbum.filter(ImageFilter.GaussianBlur(GAUSSIANBLUR))


#
# ST7789 LCD クラス
#
lcdDisp = ST7789.ST7789(
    height=240,
    rotation=90,
    port=0,
#    cs=1,
    cs=ST7789.BG_SPI_CS_FRONT,
    dc=9,
    backlight=13,
    spi_speed_hz=80 * 1000 * 1000,
    offset_left=0,
    offset_top=0
)

#
#　GPIOの初期化　コールバック関数定義
#
#　初期化 入力モードとプルアップ指定
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# コールバック関数　volumioにボタンに対応したコマンドを送信
def handle_button(pin):
    global panelMode

    if pin == 16:
        panelMode = (panelMode % 2) + 1
        return

    if panelMode == 1:
        cmd = VOLUMIO_CMD + GPIO_COMMANDS[GPIO_BUTTONS.index(pin)]
    elif panelMode == 2:
        if pin == 6:
            cmd = VOLUMIO_CMD + GPIO_COMMANDS[4]
        if pin == 20:
            cmd = VOLUMIO_CMD + GPIO_COMMANDS[5]
        if pin ==  5:
            lcdDraw.text((pTitleX,pTitleY),"SHUTDOWN START",font=smallFontTitle,fill=(255,0,0))
            os.system("sudo shutdown -h now")
            lcdDisp.display(lcdImage)
            time.sleep(120)
    
    requests.get(cmd)


#　GPIOピンにコールバック関数を定義
for pin in GPIO_BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=500)

#
#　ＬＣＤの初期化
#
lcdDisp.begin()
LCDw = lcdDisp.width
LCDh = lcdDisp.height

#print (vars(lcdDisp))

lcdImage = Image.new('RGBA',(LCDw,LCDh),color=(0,0,0,0))
lcdDraw  = ImageDraw.Draw(lcdImage)

panel11Img = Image.open(scriptPath + "/panelPic/LcdPanel11.png").convert('RGBA').resize((LCDw,LCDh))
panel12Img = Image.open(scriptPath + "/panelPic/LcdPanel12.png").convert('RGBA').resize((LCDw,LCDh))
panel21Img = Image.open(scriptPath + "/panelPic/LcdPanel21.png").convert('RGBA').resize((LCDw,LCDh))

#
#　volumioのステータス読み込み
#
#    前の情報
curStatus = { "status" : " ", "title" : " ", "artist" : " ", "album" : " " , "albumArtUrl" : " ", "volume" : " ", "seek" : " ", "duration" : " "}
prvStatus = curStatus.copy()

VolumioStatus()
GetAlbumArt()

# AutoStart
cmd = VOLUMIO_CMD + "play"
requests.get(cmd)

sizeTitle  = lcdDraw.textsize(curStatus["title"],smallFontTitle)
sizeArtist = lcdDraw.textsize(curStatus["artist"],smallFontArtist)
sizeAlbum  = lcdDraw.textsize(curStatus["album"],smallFontAlbum)

#
# 表示用の下地準備
#
while True:
    VolumioStatus()

    if curStatus["albumArtUrl"] != prvStatus["albumArtUrl"]:
        GetAlbumArt()

    lcdImage.paste(imageAlbum)		# lcdImage = imageAlbum.copy()  が思った通り動かない

    if panelMode == 1:
        if curStatus["status"] == "play":
            lcdImage = Image.alpha_composite(lcdImage,panel12Img)
        else:
            lcdImage = Image.alpha_composite(lcdImage,panel11Img)
    else:
        lcdImage = Image.alpha_composite(lcdImage,panel21Img)

    lcdDraw  = ImageDraw.Draw(lcdImage)

    sizeTitle  = lcdDraw.textsize(curStatus["title"],smallFontTitle)
    sizeArtist = lcdDraw.textsize(curStatus["artist"],smallFontArtist)
    sizeAlbum  = lcdDraw.textsize(curStatus["album"],smallFontAlbum)

    if sizeTitle[0] <= LCDw:
        pTitleX = (LCDw - sizeTitle[0])  / 2
    else:
        if pTitleX < -sizeTitle[0]:
            pTitleX = LCDw
        else:
            pTitleX -= SCROLL_WIDTH

    if sizeArtist[0] <= LCDw:
        pArtistX = (LCDw - sizeArtist[0]) / 2
    else:
        if pArtistX < -sizeArtist[0]:
            pArtistX = LCDw
        else:
            pArtistX -= SCROLL_WIDTH

    if sizeAlbum[0] <= LCDw:
        pAlbumX = (LCDw - sizeAlbum[0]) / 2
    else:
        if pAlbumX < -sizeAlbum[0]:
            pAlbumX = LCDw
        else:
            pAlbumX -= SCROLL_WIDTH

    lcdDraw.text((pTitleX,pTitleY),curStatus["title"],font=smallFontTitle,fill=(255,255,255))
    lcdDraw.text((pArtistX,pArtistY),curStatus["artist"],font=smallFontArtist,fill=(255,255,255))
    lcdDraw.text((pAlbumX,pAlbumY),curStatus["album"],font=smallFontAlbum,fill=(255,255,255))

    tVol = curStatus["volume"] / 100.0 * 182 + 22
    lcdDraw.rectangle((22,183,tVol,191),fill=(255,255,255))
    try:
        tPos = curStatus["seek"] / (curStatus["duration"] * 1000) * 228 + 6
        lcdDraw.rectangle((6,210,tPos,224),fill=(255,255,255))
    except:
        tPos = 0

    lcdDisp.display(lcdImage)

    prvStatus = curStatus.copy()

    time.sleep(0.1)
