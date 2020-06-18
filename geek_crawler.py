# -*- coding: utf-8 -*-
# !/usr/bin/python
"""=========================================
@author: Tenma
@file: geek_crawler.py
@create_time: 2020/4/23 12:29
@file specification: 极客时间课程爬取脚本
    极客时间官网地址：https://time.geekbang.org/
    流程： 登录账号 -- 获取课程列表（专栏） -- 循环读取单个专栏的内容 -- 将内容保存成 md 文件）
========================================="""
import time
import datetime
import requests
import re
from copy import deepcopy
import logging
import os
import pathlib


# 定义日志相关内容
logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO)
handler = logging.FileHandler(filename='geek_crawler.log', mode='w', encoding='utf-8')
log = logging.getLogger(__name__)
log.addHandler(handler)

# 定义全局变量
FINISH_ARTICLES = []
ALL_ARTICLES = []


class RequestError(Exception):
    """ 请求错误 """
    pass


class NotValueError(Exception):
    """ 没有内容错误 """
    pass


def _load_finish_article():
    """ 将当前目录下已遍历过文章 ID 文件中的数据加载到内存中 """
    result = []
    _dir = pathlib.PurePosixPath()
    file_path = os.path.abspath(_dir / 'finish_crawler_article.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for article_id in f.readlines():
                article_id = article_id.strip('\n')
                if article_id:
                    result.append(article_id)
    return list(set(result))


def _save_finish_article_id_to_file():
    """ 将已经遍历完成的文章 ID 保存成文本，后面不用再遍历 """
    global FINISH_ARTICLES
    _dir = pathlib.PurePosixPath()
    file_path = os.path.abspath(_dir / 'finish_crawler_article.txt')
    with open(file_path, 'a+', encoding='utf-8') as f:
        for i in FINISH_ARTICLES:
            f.write(str(i) + '\n')


def check_filename(file_name):
    """
    校验文件名称的方法，在 windows 中文件名不能包含('\','/','*','?','<','>','|') 字符
    Args:
        file_name: 文件名称
    Returns:
        修复后的文件名称
    """
    return file_name.replace('\\', '') \
                    .replace('/', '') \
                    .replace('*', 'x') \
                    .replace('?', '') \
                    .replace('<', '《') \
                    .replace('>', '》') \
                    .replace('|', '_') \
                    .replace('\n', '') \
                    .replace('\b', '') \
                    .replace('\f', '') \
                    .replace('\t', '') \
                    .replace('\r', '')


class Cookie:
    def __init__(self, cookie_string=None):
        self._cookies = {}
        if cookie_string:
            self.load_string_cookie(cookie_string)

    @property
    def cookie_string(self):
        """
        将对象的各属性转换成字符串形式的 Cookies
        Returns:
            字符串形式的 cookies，方便给 HTTP 请求时使用
        """
        return ';'.join([f'{k}={v}' for k, v in self._cookies.items()])

    def set_cookie(self, key, value):
        self._cookies[key] = value

    @staticmethod
    def list_to_dict(lis):
        """
        列表转换成字典的方法
        Args:
            lis: 列表内容
        Returns:
            转换后的字典
        """
        result = {}
        for ind in lis:
            try:
                ind = ind.split('=')
                result[ind[0]] = ind[1]
            except IndexError:
                continue
        return result

    def load_string_cookie(self, cookie_str):
        """
        从字符串中加载 Cookie 的方法（将字符串转换成字典形式）, 相当于 cookie_string 方法的逆反操作
        Args:
            cookie_str: 字符串形式的 Cookies，一般是从抓包请求中复制过来
                eg: gksskpitn=cc662cd7-0a39-430a-a603-a1c61d6f784f; LF_ID=1587783958277-6056470-8195597;
        Returns:
        """
        cookie_list = cookie_str.split(';')
        res = self.list_to_dict(cookie_list)
        self._cookies = {**self._cookies, **res}

    def load_set_cookie(self, set_cookie):
        """
        从抓包返回的 Response Headers 中的 set-cookie 中提取 cookie 的方法
        Args:
            set_cookie: set-cookie 的值
        Returns:
        """
        set_cookie = re.sub(".xpires=.*?;", "", set_cookie)
        cookies_list = set_cookie.split(',')
        cookie_list = []
        for cookie in cookies_list:
            cookie_list.append(cookie.split(';')[0])
        res = self.list_to_dict(cookie_list)
        self._cookies = {**self._cookies, **res}

    def __repr__(self):
        return f'The cookies is : {self._cookies}'


class GeekCrawler:
    """ 极客时间相关操作的类 """
    def __init__(self, cellphone=None, passwd=None, exclude=None):
        self.cellphone = cellphone
        self.password = passwd
        self._check()
        self.cookie = Cookie("LF_ID=1587783958277-6056470-8195597;_ga=GA1.2.880710184.1587783959;"
                             "_gid=GA1.2.1020649675.1587783959; SERVERID=1fa1f330efedec1559b3abbc"
                             "b6e30f50|1587784166|1587783958; _gat=1;Hm_lvt_022f847c4e3acd44d4a24"
                             "81d9187f1e6=1587775851,1587775917,1587783916,1587784202; Hm_lpvt_02"
                             "2f847c4e3acd44d4a2481d9187f1e6=1587784202;")
        self.common_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) "
                          "AppleWebKit/537.36 (KHTML, like Gecko)Chrome/81.0.4044.122 Safari/537.36"
        }
        self.products = []
        self.exclude = exclude

    def _check(self):
        if not self.cellphone:
            self.cellphone = str(input('请输入你要登录的手机号： '))
        if not self.password:
            self.password = str(input('请输入你极客账号的登录密码： '))

    def _login(self):
        """ 登录接口方法 """
        log.info("请求登录接口：")
        url = "https://account.geekbang.org/account/ticket/login"
        method = "POST"
        headers = deepcopy(self.common_headers)
        headers["Host"] = "account.geekbang.org"
        headers["Origin"] = "https://account.geekbang.org"
        headers["Cookie"] = self.cookie.cookie_string
        params = {
            "country": 86,
            "cellphone": self.cellphone,
            "password": self.password,
            "captcha": "",
            "remember": 1,
            "platform": 3,
            "appid": 1,
            "source": ""
        }

        log.info(f"接口请求参数：{params}")
        res = requests.request(method, url, headers=headers, json=params)

        if (res.status_code != 200) or (str(res.json().get('code', '')) == '-1'):
            _save_finish_article_id_to_file()
            log.info(f"此时 products 的数据为：{self.products}")
            log.error(f"登录接口请求出错，返回内容为：{res.content.decode()}")
            raise RequestError(f"登录接口请求出错，返回内容为：{res.content.decode()}")
        self.cookie.load_set_cookie(res.headers['Set-Cookie'])
        log.info('-'*40)

    def _user_auth(self):
        """ 用户认证接口方法 """
        log.info("请求用户认证接口：")
        now_time = int(time.time() * 1000)
        url = f"https://account.geekbang.org/serv/v1/user/auth?t={now_time}"
        method = "GET"
        headers = deepcopy(self.common_headers)
        headers["Host"] = "account.geekbang.org"
        headers["Origin"] = "https://time.geekbang.org"
        headers["Cookie"] = self.cookie.cookie_string

        res = requests.request(method, url, headers=headers)

        if (res.status_code != 200) or (str(res.json().get('code', '')) != '0'):
            _save_finish_article_id_to_file()
            log.info(f"此时 products 的数据为：{self.products}")
            log.error(f"用户认证接口请求出错，返回内容为：{res.json()}")
            raise RequestError(f"用户认证接口请求出错，返回内容为：{res.json()}")
        self.cookie.load_set_cookie(res.headers['Set-Cookie'])
        log.info('-' * 40)


    def _product(self, _type='c1'):
        """ 商品列表（就是课程）的接口）方法 """
        log.info("请求获取课程列表接口：")
        url = "https://time.geekbang.org/serv/v3/learn/product"
        method = "POST"
        headers = deepcopy(self.common_headers)
        headers["Host"] = "time.geekbang.org"
        headers["Origin"] = "https://time.geekbang.org"
        headers["Cookie"] = self.cookie.cookie_string
        params = {
            "desc": 'true',
            "expire": 1,
            "last_learn": 0,
            "learn_status": 0,
            "prev": 0,
            "size": 20,
            "sort": 1,
            "type": "",
            "with_learn_count": 1
        }

        log.info(f"接口请求参数：{params}")
        res = requests.request(method, url, headers=headers, json=params)

        if res.status_code != 200:
            log.info(f"此时 products 的数据为：{self.products}")
            log.error(f"课程列表接口请求出错，返回内容为：{res.content.decode()}")
            raise RequestError(f"课程列表接口请求出错，返回内容为：{res.content.decode()}")
        data = res.json().get('data', {})
        self.cookie.load_set_cookie(res.headers['Set-Cookie'])

        if data:
            self.products += self._parser_products(data, _type)
        else:
            _save_finish_article_id_to_file()
            log.info(f"此时 products 的数据为：{self.products}")
            log.error(f"课程列表接口没有获取到内容，请检查请求。返回结果为：{res.content.decode()}")
            raise NotValueError(f"课程列表接口没有获取到内容，请检查请求。返回结果为：{res.content.decode()}")
        log.info('-' * 40)

    def _parser_products(self, data, _type='c1'):
        """
        解析课程列表内容的方法（从中提取部分数据）
        Args:
            data: 课程相关信息，一般为接口返回的数据
            _type: 课程类型，c1 代表专栏，all 代表全部, 默认只获取专栏的内容
        Returns:
            解析后的结果，以列表形式
        """
        result = []
        keys = ['title', 'type', 'id']  # 定义要拿取的字段
        products = data.get('products', [])
        lists = data.get('list', [])
        for product in products:
            # 如果课程标题在需要排除的列表中，则跳过该课程
            if product.get('title', '') in self.exclude:
                continue

            new_product = {key: value for key, value in product.items() if key in keys}
            new_product['articles'] = []  # 定义文章列表（用来存储文章信息）
            new_product['article_ids'] = []  # 定义文章 ID 列表（用来存储文章 ID 信息） ）
            for pro in lists:
                if new_product['id'] == pro['pid']:
                    new_product['aid'] = pro['aid']
            if _type.lower() == 'all' or new_product['type'] == _type:
                result.append(new_product)
        return result

    def _article(self, aid, pro, file_type=None, get_comments=False):
        """ 通过课程 ID 获取文章信息接口方法 """
        global FINISH_ARTICLES
        log.info("请求获取文章信息接口：")
        url = "https://time.geekbang.org/serv/v1/article"
        method = "POST"
        headers = deepcopy(self.common_headers)
        headers["Host"] = "time.geekbang.org"
        headers["Origin"] = "https://time.geekbang.org"
        headers["Cookie"] = self.cookie.cookie_string
        params = {
            "id": aid,
            "include_neighbors": "true",
            "is_freelyread": "true"
        }

        log.info(f"接口请求参数：{params}")
        res = requests.request(method, url, headers=headers, json=params)

        if res.status_code != 200:
            _save_finish_article_id_to_file()
            log.info(f"此时 products 的数据为：{self.products}")
            log.error(f"获取文章信息接口请求出错，返回内容为：{res.content.decode()}")
            raise RequestError(f"获取文章信息接口请求出错，返回内容为：{res.content.decode()}")
        data = res.json().get('data', {})
        self.cookie.load_set_cookie(res.headers['Set-Cookie'])

        if data:
            comments = self._comments(aid) if get_comments else None
            keys = ['article_content', 'article_title', 'id', 'audio_download_url']  # 定义要拿取的字段
            article = {key: value for key, value in data.items() if key in keys}
            self.save_to_file(
                pro['title'],
                article['article_title'],
                article['article_content'],
                audio=article['audio_download_url'],
                file_type=file_type,
                comments=comments
            )

            FINISH_ARTICLES.append(article['id'])  # 将该文章 ID 加入到遍历完成的列表中
            pro['cid'] = data['cid']
            # pro['articles'].append(article)  # 将文章信息添加到列表中
        else:
            _save_finish_article_id_to_file()
            log.info(f"此时 products 的数据为：{self.products}")
            log.error(f"获取文章信息接口没有获取到内容，请检查请求。返回结果为：{res.content.decode()}")
            raise NotValueError(f"获取文章信息接口没有获取到内容，请检查请求。返回结果为：{res.content.decode()}")
        log.info('-' * 40)

    def _comments(self, aid):
        """ 获取文章评论详情接口 """
        log.info("请求获取文章评论详情接口：")
        url = "https://time.geekbang.org/serv/v1/comments"
        method = "POST"
        headers = deepcopy(self.common_headers)
        headers["Host"] = "time.geekbang.org"
        headers["Origin"] = "https://time.geekbang.org"
        headers["Cookie"] = self.cookie.cookie_string
        params = {
            "aid": aid,
            "prev": "0"
        }

        log.info(f"接口请求参数：{params}")
        res = requests.request(method, url, headers=headers, json=params)

        if res.status_code != 200:
            log.error(f"获取文章评论接口请求出错，返回内容为：{res.content.decode()}")
            return None
        data = res.json().get('data', {}).get('list', [])
        self.cookie.load_set_cookie(res.headers['Set-Cookie'])

        if data:
            keys = ['comment_content', 'comment_ctime', 'user_header', 'user_name', 'replies']  # 定义要拿取的字段
            comments = [{key: value for key, value in comment.items() if key in keys} for comment in data]
            return comments
        else:
            return None

    def _articles(self, cid, pro):
        """ 获取文章列表接口方法 """
        global ALL_ARTICLES
        log.info("请求获取文章列表接口：")
        url = "https://time.geekbang.org/serv/v1/column/articles"
        method = "POST"
        headers = deepcopy(self.common_headers)
        headers["Host"] = "time.geekbang.org"
        headers["Origin"] = "https://time.geekbang.org"
        headers["Cookie"] = self.cookie.cookie_string
        params = {
            "cid": cid,
            "size": 100,
            "prev": 0,
            "order": "earliest",
            "sample": "false"
        }

        log.info(f"接口请求参数：{params}")
        res = requests.request(method, url, headers=headers, json=params)

        if res.status_code != 200:
            _save_finish_article_id_to_file()
            log.info(f"此时 products 的数据为：{self.products}")
            log.error(f"获取文章列表接口请求出错，返回内容为：{res.json()}")
            raise RequestError(f"获取文章列表接口请求出错，返回内容为：{res.json()}")
        data = res.json().get('data', {})
        self.cookie.load_set_cookie(res.headers['Set-Cookie'])

        if data:
            ids = []
            article_list = data.get('list', [])
            for article in article_list:
                ids.append(article['id'])
            ALL_ARTICLES += ids
            pro['article_ids'] += ids
        else:
            _save_finish_article_id_to_file()
            log.info(f"此时 products 的数据为：{self.products}")
            log.error(f"获取文章列表接口没有获取到内容，请检查请求。返回结果为：{res.json()}")
            raise NotValueError(f"获取文章列表接口没有获取到内容，请检查请求。返回结果为：{res.json()}")
        log.info('-' * 40)

    @staticmethod
    def save_to_file(dir_name, filename, content, audio=None, file_type=None, comments=None):
        """
        将结果保存成文件的方法，保存在当前目录下
        Args:
            dir_name: 文件夹名称，如果不存在该文件夹则会创建文件夹
            filename: 文件名称，直接新建
            content: 需要保存的文本内容
            audio: 需要填入文件中的音频文件（一般为音频地址）
            file_type: 文档类型（需要保存什么类型的文档），默认保存为 Markdown 文档
            comments: 评论相关数据
        Returns:
        """
        if not file_type: file_type = '.md'
        dir_path = pathlib.PurePosixPath() / dir_name
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)
        filename = check_filename(filename)
        file_path = os.path.abspath(dir_path / (filename + file_type))

        # 处理评论数据
        temp = ""
        if comments:
            with open('comment.css', 'r', encoding='utf-8') as f:
                comment_style = f.read()
            temp = comment_style + "<ul>"
            for comment in comments:
                replie_str = ""
                for replie in comment.get('replies', []):
                    replie_str += f"""<p class="_3KxQPN3V_0">{replie['user_name']}: {replie['content']}</p>"""
                comment_str = f"""<li>
<div class="_2sjJGcOH_0"><img src="{comment['user_header']}"
  class="_3FLYR4bF_0">
<div class="_36ChpWj4_0">
  <div class="_2zFoi7sd_0"><span>{comment['user_name']}</span>
  </div>
  <div class="_2_QraFYR_0">{comment['comment_content']}</div>
  <div class="_10o3OAxT_0">
    {replie_str}
  </div>
  <div class="_3klNVc4Z_0">
    <div class="_3Hkula0k_0">{datetime.datetime.fromtimestamp(comment['comment_ctime'])}</div>
  </div>
</div>
</div>
</li>\n"""
                temp += comment_str
            temp += "</ul>"

        # 将所有数据写入文件中
        with open(file_path, 'w', encoding='utf-8') as f:
            if audio:
                audio_text = f'<audio title="{filename}" src="{audio}" controls="controls"></audio> \n'
                f.write(audio_text)
            f.write(content + temp)


def run(cellphone=None, passwd=None, exclude=None, file_type=None, get_comments=False):
    """ 整体流程的请求方法 """
    global FINISH_ARTICLES
    global ALL_ARTICLES

    geek = GeekCrawler(cellphone, passwd, exclude=exclude)
    geek._login()  # 请求登录接口进行登录
    geek._product()  # 请求获取课程接口

    number = 0

    for pro in geek.products:
        geek._articles(pro['id'], pro)  # 获取文章列表

        article_ids = pro['article_ids']
        for aid in article_ids:
            if set(ALL_ARTICLES) == set(FINISH_ARTICLES):
                import sys
                log.info("正常抓取完成啦，不用再继续跑脚本了。")
                sys.exit(1)

            if str(aid) in FINISH_ARTICLES:
                continue
            geek._article(aid, pro, file_type=file_type, get_comments=get_comments)  # 获取单个文章的信息
            time.sleep(5)  # 做一个延时请求，避免过快请求接口被限制访问
            number += 1
            # 判断是否连续抓取过 37次，如果是则暂停 10s
            if number == 37:
                log.info("抓取达到37次了，先暂停 10s 再继续。")
                time.sleep(10)
                number = 0  # 重新计数
                geek._user_auth()
    _save_finish_article_id_to_file()
    log.info("正常抓取完成。")


if __name__ == "__main__":
    # 采用在脚本中写死账号密码的方式
    # cellphone = ""
    # pwd = ""

    # 采用每次跑脚本手动输入账号密码的方式
    cellphone = str(input("请输入你的极客时间账号（手机号）: "))
    pwd = str(input("请输入你的极客时间密码: "))

    # 需要排除的课程列表，根据自己的情况定义（比如已经有的资源就不用再继续下载了）
    # exclude = ['左耳听风', '趣谈网络协议']
    exclude = []

    # 需要保存文件的后缀名，尽量选 .md 或者 .html
    file_type = '.md'

    # 是否获取评论信息，目前暂时设置为不获取，因为 md 文档中评论显示不太好看，如果需要获取评论的话请设置保存文本为 HTML（样式好看些）
    get_comments = False  # True

    try:
        FINISH_ARTICLES = _load_finish_article()
        run(cellphone, pwd, exclude=exclude, get_comments=get_comments)
    except Exception:
        import traceback
        log.error(f"请求过程中出错了，出错信息为：{traceback.format_exc()}")
    finally:
        _save_finish_article_id_to_file()
