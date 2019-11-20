from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
import os


def SetMp3Info(path, info):
    songFile = ID3(path)
    # songFile['APIC'] = APIC(  # 插入封面
    #     encoding=3,
    #     mime='image/jpeg',
    #     type=3,
    #     desc=u'Cover',
    #     data=info['picData']
    # )
    songFile['TIT2'] = TIT2(  # 插入歌名
        encoding=3,
        text=info['title']
    )
    songFile['TPE1'] = TPE1(  # 插入第一演奏家、歌手、等
        encoding=3,
        text=info['artist']
    )
    songFile['TALB'] = TALB(  # 插入专辑名
        encoding=3,
        text=info['album']
    )
    songFile.save()

if __name__ == '__main__':
    picPath = 'icon.png'
    with open(picPath, 'rb') as f:
        picData = f.read()
    info = {'picData': picData, 'title': '你的酒馆对我打了烊',
            'artist': '陈雪凝', 'album': '绿色'}
    songPath = '赵雷 - 成都.mp3'
    SetMp3Info(songPath, info)