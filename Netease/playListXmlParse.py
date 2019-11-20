#!/usr/bin/python3

import requests, hashlib, sys, click, re, base64, binascii, json, os
from Crypto.Cipher import AES
from http import cookiejar
from xml.dom.minidom import parse
import xml.dom.minidom
import html


def parseAllSongForString(htmlString) :
   res = searchList(htmlString)
   if res:
      return findAllSong(res)

# def parseAllSongForListHtml(htmlStr) :
#    for xmlNum, xmlString in enumerate(htmlStr):
#       # print('num',xmlNum, xmlString)
#       searchL = searchList(xmlString)
#       if searchL:
#          findAllSong(searchL)

def searchList(xmlString) :
   searchObj = re.search('<ul class="f-hide">.*</ul>', xmlString)
   if searchObj:
      # print("searchObj.group() : ", searchObj.group())
      res = re.sub('(<ul class="f-hide">)|(</ul>)|(</a></li>)', '', searchObj.group())
      return res
   # else:
      # print("Nothing found!!")

def findAllSong(allSongstring) :
   pattern = re.compile(r'<li><a href="/song\?id=')
   result = re.split(pattern,allSongstring)
   # print(result)
   return result
  
def parseSongInfoForHtml(htmlString) :
   '''
   <p class="des s-fc4">歌手：<span title="毛不易"><a class="s-fc7" href="/artist?id=12138269" >毛不易</a></span></p>
   <p class="des s-fc4">所属专辑：<a href="/album?id=39483040" class="s-fc7">平凡的一天</a></p>
   '''
   search_artist = re.search(r'<p class="des s-fc4">歌手：<span title=".*"><a class="s-fc7" href=', htmlString)
   # print(search_artist)
   if search_artist :
      artist = re.sub('(<p class="des s-fc4">歌手：<span title=")|("><a class="s-fc7" href=)', '', search_artist.group())
   # print(artist)
   # print(htmlString)
   search_album = re.search(r'(<p class="des s-fc4">所属专辑：<a href="/album\?id=).*(</a><)', htmlString)
   if search_album :
      album_re = re.sub('</a><', '', search_album.group())
      # print(album_re)
      pattern = re.compile(r'class="s-fc7">')
      album_list = re.split(pattern, album_re)
      if len(album_list) == 2 :
         album = album_list[1]
         # print(album)
   
   res = {}
   if artist :
      res['artist'] = artist
   
   if album :
      res['album'] = album
   
   return res

if __name__ == '__main__':

   print('--------start')

   music_list_name = 'movies.xml'
	# 如果music列表存在, 那么开始下载
   if os.path.exists(music_list_name):
      with open(music_list_name, 'r') as f:
         musiclist = f.readlines()
         # print(musiclist)
         parseAllSong(musiclist)
         

            