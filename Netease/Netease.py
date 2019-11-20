# -*- coding:utf-8 -*-
import requests, hashlib, sys, click, re, base64, binascii, json, os
from Crypto.Cipher import AES
from http import cookiejar
from xml.dom.minidom import parse
import xml.dom.minidom
import html
import playListXmlParse
import MP3Info


"""
Website:http://cuijiahua.com
Author:Jack Cui
Refer:https://github.com/darknessomi/musicbox
"""

class Encrypyed():
	"""
	解密算法
	"""
	def __init__(self):
		self.modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
		self.nonce = '0CoJUm6Qyw8W8jud'
		self.pub_key = '010001'

	# 登录加密算法, 基于https://github.com/stkevintan/nw_musicbox脚本实现
	def encrypted_request(self, text):
		text = json.dumps(text)
		sec_key = self.create_secret_key(16)
		enc_text = self.aes_encrypt(self.aes_encrypt(text, self.nonce), sec_key.decode('utf-8'))
		enc_sec_key = self.rsa_encrpt(sec_key, self.pub_key, self.modulus)
		data = {'params': enc_text, 'encSecKey': enc_sec_key}
		return data

	def aes_encrypt(self, text, secKey):
		pad = 16 - len(text) % 16
		text = text + chr(pad) * pad
		encryptor = AES.new(secKey.encode('utf-8'), AES.MODE_CBC, b'0102030405060708')
		ciphertext = encryptor.encrypt(text.encode('utf-8'))
		ciphertext = base64.b64encode(ciphertext).decode('utf-8')
		return ciphertext

	def rsa_encrpt(self, text, pubKey, modulus):
		text = text[::-1]
		rs = pow(int(binascii.hexlify(text), 16), int(pubKey, 16), int(modulus, 16))
		return format(rs, 'x').zfill(256)

	def create_secret_key(self, size):
		return binascii.hexlify(os.urandom(size))[:16]


class Song():
	"""
	歌曲对象，用于存储歌曲的信息
	"""
	def __init__(self, song_id, song_name, song_num, song_url=None):
		self.song_id = song_id
		self.song_name = song_name
		self.song_num = song_num
		self.song_url = '' if song_url is None else song_url
		self.song_title = song_name
		self.song_artist = ''
		self.song_album = ''

class Crawler():
	"""
	网易云爬取API
	"""
	def __init__(self, timeout=60, cookie_path='.'):
		self.headers = {
			'Accept': '*/*',
			'Accept-Encoding': 'gzip,deflate,sdch',
			'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
			'Connection': 'keep-alive',
			'Content-Type': 'application/x-www-form-urlencoded',
			'Host': 'music.163.com',
			'Referer': 'http://music.163.com/search/',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
		}
		self.session = requests.Session()
		self.session.headers.update(self.headers)
		self.session.cookies = cookiejar.LWPCookieJar(cookie_path)
		self.download_session = requests.Session()
		self.timeout = timeout
		self.ep = Encrypyed()

	def get_request(self, url):
		"""
		Get请求
		:return: 字典
		"""
		headers = {
			"Accept": "*/*",
			"Accept-Encoding": "br,gzip,deflate",
			'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4;',
			'Referer': 'http://music.163.com/search/',
			'Content-Type': 'text/html;charset=utf8',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
		}
		# 'Referer':'https://music.163.com/discover/playlist',
		# 'Referer': 'https://music.163.com/user/home?id=376807422',
		# print('aaaaaaaaaaaaaaaaa')
		resp = requests.get(url=url,headers=headers)
		# print('bbbbbbbbbbb')
		# print(resp.status_code)
		# print(resp.reason)
		if resp.status_code != 200 :  # 获取响应状态码
			click.echo('get_request error')
		else :
			return resp.content # 获取响应消息

	def post_request(self, url, params):
		"""
		Post请求
		:return: 字典
		"""

		data = self.ep.encrypted_request(params)
		resp = self.session.post(url, data=data, timeout=self.timeout)
		result = resp.json()
		if result['code'] != 200:
			click.echo('post_request error')
		else:
		    return result

	def playList(self, listId):
		"""
		搜索API
		:params listId: 歌单id
		:return: html.
		"""

		url = 'https://music.163.com/playlist?id='+listId
		print('获取列表：'+url)
		result = self.get_request(url)
		return result

	def search(self, search_content, search_type, limit=9):
		"""
		搜索API
		:params search_content: 搜索内容
		:params search_type: 搜索类型
		:params limit: 返回结果数量
		:return: 字典.
		"""

		url = 'http://music.163.com/weapi/cloudsearch/get/web?csrf_token='
		params = {'s': search_content, 'type': search_type, 'offset': 0, 'sub': 'false', 'limit': limit}
		result = self.post_request(url, params)
		return result

	def search_song(self, song_name, song_num, quiet=True, limit=9):
		"""
		根据音乐名搜索
		:params song_name: 音乐名
		:params song_num: 下载的歌曲数
		:params quiet: 自动选择匹配最优结果
		:params limit: 返回结果数量
		:return: Song独享
		"""

		result = self.search(song_name, search_type=1, limit=limit)

		if result['result']['songCount'] <= 0:
			click.echo('Song {} not existed.'.format(song_name))
		else:
			songs = result['result']['songs']
			if quiet:
				song_id, song_name = songs[0]['id'], songs[0]['name']
				song = Song(song_id=song_id, song_name=song_name, song_num=song_num)
				return song

	def get_song_url(self, song_id, bit_rate=320000):
		"""
		获得歌曲的下载地址
		:params song_id: 音乐ID<int>.
		:params bit_rate: {'MD 128k': 128000, 'HD 320k': 320000}
		:return: 歌曲下载地址
		"""

		url = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='
		csrf = ''
		params = {'ids': [song_id], 'br': bit_rate, 'csrf_token': csrf}
		result = self.post_request(url, params)
		# 歌曲下载地址
		song_url = result['data'][0]['url']

		# 歌曲不存在
		if song_url is None:
			click.echo('Song {} is not available due to copyright issue.'.format(song_id))
		else:
			return song_url

	def get_song_info_meta(self, song_name, song_id):
		'''
		获取音乐的描述信息
		:params song_name: 音乐名
		:params song_id: 音乐ID<int>.
		:return: 歌曲信息
		'''
		headers = {
			"Accept": "*/*",
			"Accept-Encoding": "br,gzip,deflate",
			'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4;',
			'Referer': 'https://music.163.com/',
			'Content-Type': 'text/html;charset=utf8',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
		}
		# 'Referer':'https://music.163.com/discover/playlist',
		# 'Referer': 'https://music.163.com/user/home?id=376807422',
		info_url = 'http://music.163.com/song?id={}'.format(song_id)
		# print(info_url)
		resp = requests.get(url=info_url,headers=headers)
		# print('获取歌曲信息bbbbbbbbbbbbbbbbb')
		# print(resp.status_code)
		# print(resp.reason)
		if resp.status_code != 200 :  # 获取响应状态码
			click.echo('get_song_info_meta error')
		else :
			return resp.content # 获取响应消息

	def get_song_by_url(self, song_url, song_name, song_artist, song_num, folder):
		"""
		下载歌曲到本地
		:params song_url: 歌曲下载地址
		:params song_name: 歌曲名字
		:params song_num: 下载的歌曲数
		:params folder: 保存路径
		"""
		if not os.path.exists(folder):
			os.makedirs(folder)
		# fpath = os.path.join(folder, str(song_num) + '_' + song_name + '.mp3')
		fpath = os.path.join(folder, song_artist + ' - ' + song_name + '.mp3')
		if sys.platform == 'win32' or sys.platform == 'cygwin':
			valid_name = re.sub(r'[<>:"/\\|?*]', '', song_name)
			if valid_name != song_name:
				click.echo('{} will be saved as: {}.mp3'.format(song_name, valid_name))
				fpath = os.path.join(folder, valid_name + '.mp3')
		
		if not os.path.exists(fpath):
			resp = self.download_session.get(song_url, timeout=self.timeout, stream=True)
			length = int(resp.headers.get('content-length'))
			label = 'Downloading {} {}kb'.format(song_name, int(length/1024))

			with click.progressbar(length=length, label=label) as progressbar:
				with open(fpath, 'wb') as song_file:
					for chunk in resp.iter_content(chunk_size=1024):
						if chunk:
							song_file.write(chunk)
							progressbar.update(1024)


class Netease():
	"""
	网易云音乐下载
	"""
	def __init__(self, timeout, folder, quiet, cookie_path):
		self.crawler = Crawler(timeout, cookie_path)
		self.folder = '.' if folder is None else folder
		self.quiet = quiet

	def get_play_list(self, listId):
		"""
		根据歌单ID获取歌单列表
		:params listId: 歌单ID
		"""

		try:
			list = self.crawler.playList(listId)
		except:
			click.echo('get_play_list error')
		# 如果找到了音乐, 则下载
		if list != None:
			# self.download_song_by_id(song.song_id, song.song_name, song.song_num, self.folder)
			# self.download_song_by_id('4331105', 'Loves Me Not', '1', self.folder)
			self.parse_play_list(list)

	def parse_play_list(self, list):
		"""
		解析列表html列表
		:params list: html 
		"""
		'''
		bytes 与 str 格式互转
		解决办法非常的简单，只需要用上python的bytes和str两种类型转换的函数encode()、decode()即可！
		str通过encode()方法可以编码为指定的bytes；
		反过来，如果我们从网络或磁盘上读取了字节流，那么读到的数据就是bytes。要把bytes变为str，就需要用decode()方法；
		text = list.decode()
		'''
		'''
		使用minidom解析器打开 XML 文档
		1、unescap - 反转义  escape - 转义 
		import html
		text = html.escape(list.decode())

		2、 过滤特殊字符
		text = re.sub(u"[\x00-\x08\x0b-\x0c\x0e-\x1f]+",u"",text)

		3、 dom 解析 
		https://www.runoob.com/python3/python3-xml-processing.html

		DOMTree = xml.dom.minidom.parseString(text)
		collection = DOMTree.documentElement
		if collection.hasAttribute("shelf"):
			print ("Root element : %s" % collection.getAttribute("shelf"))
		# 在集合中获取所有电影
		ul = collection.getElementsByTagName("ul")
		print(ul)
		# 打印每部电影的详细信息
		for movie in ul:
			print ("*****Movie*****")
		if movie.hasAttribute("title"):
			print ("Title: %s" % movie.getAttribute("title"))

		type = movie.getElementsByTagName('type')[0]
		print ("Type: %s" % type.childNodes[0].data)
		format = movie.getElementsByTagName('format')[0]
		print ("Format: %s" % format.childNodes[0].data)
		rating = movie.getElementsByTagName('rating')[0]
		print ("Rating: %s" % rating.childNodes[0].data)
		description = movie.getElementsByTagName('description')[0]
		print ("Description: %s" % description.childNodes[0].data)
		'''
		print('=======================start download=========')
		text = list.decode()
		# print(text)
		songlist = playListXmlParse.parseAllSongForString(text)
		pattern = re.compile(r'">')
		num = 0
		for song in songlist:
			# print(song)
			result = re.split(pattern,song)
			if len(result) == 2 :
				print('num:',num,'----------------------------------')
				print(result)
				self.download_song_by_id(result[0], result[1], num, self.folder)
				num = num + 1
				print('---------------------------------------------')

		print('=======================end download=======')

	def download_song_by_search(self, song_name, song_num):
		"""
		根据歌曲名进行搜索
		:params song_name: 歌曲名字
		:params song_num: 下载的歌曲数
		"""

		try:
			song = self.crawler.search_song(song_name, song_num, self.quiet)
		except:
			click.echo('download_song_by_serach error')
		# 如果找到了音乐, 则下载
		if song != None:
			self.download_song_by_id(song.song_id, song.song_name, song.song_num, self.folder)

	def getMp3Meta(self, song_id, song_name) : 
		'''
		设置歌曲信息
		'''
		try:
			res = self.crawler.get_song_info_meta(song_name, song_id)
			html_text = res.decode()
			sonDict = playListXmlParse.parseSongInfoForHtml(html_text)
			sonDict['title'] = song_name
			# print(sonDict)
		except:
			click.echo('getMp3Meta error')	
		return sonDict	

	def download_song_by_id(self, song_id, song_name, song_num, folder='.'):
		"""
		通过歌曲的ID下载
		:params song_id: 歌曲ID
		:params song_name: 歌曲名
		:params song_num: 下载的歌曲数
		:params folder: 保存地址
		"""
		try:
			url = self.crawler.get_song_url(song_id)
			info = self.getMp3Meta(song_id, song_name)
			song_artist = info['artist']
			# 去掉非法字符
			song_name = song_name.replace('/', '')
			song_name = song_name.replace('.', '')
			song_artist = song_artist.replace('/', '&')
			song_artist = song_artist.replace('.', '')
			self.crawler.get_song_by_url(url, song_name, song_artist, song_num, folder)
			pwd = os.getcwd()
			fpath = pwd + '/' + folder + '/' + song_artist + ' - ' + song_name + '.mp3'
			print('设置mp3信息....')
			MP3Info.SetMp3Info(fpath, info)
		except:
			click.echo('download_song_by_id error')


if __name__ == '__main__':
	print('--------start')
	timeout = 60
	output = 'Musics'
	quiet = True
	cookie_path = 'Cookie'
	netease = Netease(timeout, output, quiet, cookie_path)
	# ----
	play_list = netease.get_play_list('2250011882')

	exit(0)
	# ---
	music_list_name = 'music_list.txt'
	# 如果music列表存在, 那么开始下载
	if os.path.exists(music_list_name):
		with open(music_list_name, 'r') as f:
			music_list = list(map(lambda x: x.strip(), f.readlines()))
			print(music_list)

		for song_num, song_name in enumerate(music_list):
			print('num',song_num, song_name)
			netease.download_song_by_search(song_name,song_num + 1)
	else:
		click.echo('music_list.txt not exist.')