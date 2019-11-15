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

def parseAllSongForListHtml(htmlStr) :
   for xmlNum, xmlString in enumerate(htmlStr):
      # print('num',xmlNum, xmlString)
      searchL = searchList(xmlString)
      if searchL:
         findAllSong(searchL)

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
  
if __name__ == '__main__':

   print('--------start')

   music_list_name = 'movies.xml'
	# 如果music列表存在, 那么开始下载
   if os.path.exists(music_list_name):
      with open(music_list_name, 'r') as f:
         musiclist = f.readlines()
         # print(musiclist)
         parseAllSong(musiclist)
         

            