#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:gtyphoon
import argparse
import os
import re
import sys
import time
from random import randint
import requests
from selenium import webdriver
# 导入ChromeService类，用于封装chromedriver配置（Selenium 4.6.0+ 必需）
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


# 浏览器标识
AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Mobile Safari/537.36 Edg/85.0.564.67",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4094.1 Safari/537.36",
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Opera/9.80 (Windows NT 10.0; Win64; x64) Presto/2.8.131 Version/11.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4094.1 Safari/537.36",
]
n_agent = AGENT_LIST[randint(0, 9)]  # 随机选择一个请求头
# this_dir为项目目录路径。os.path.abspath(__file__)为当前文件路径，os.path.dirname()是找到该文件的所在目录
this_dir = os.path.dirname(os.path.abspath(__file__))
# 将该路径动态加入环境变量
sys.path.append(this_dir)

# 自定义解析器子类（重写 format_help 移除 options:）


def this_args():
    # 创建主解析器
    parser = argparse.ArgumentParser(description="抖音视频获取工具", exit_on_error=False,add_help=False)
    optional_group =parser.add_argument_group('可选项')
    optional_group.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,  # 隐藏在参数列表中（可选，保持美观）
        help="显示此帮助信息并退出"
    )
    optional_group.add_argument("-d", metavar='<DIR>', type=str, default=sys.path[-1] + '/video/',
                        help='设置下载目录，缺省值为当前程序video文件夹，当前目录为%(default)s')
    typem = optional_group.add_mutually_exclusive_group()
    typem.add_argument('-a', '--album', action='store_true',
                       help=f'传入某专辑内视频链接，将下载整个专辑，缺省值%(default)s')
    typem.add_argument('-u', '--userall', action='store_true',
                       help=f'传入该用户任意视频链接，将下载用户主页所有视频，缺省值%(default)s')
    # 自定义组
    urlp = parser.add_argument_group('必选项')
    urlpm = urlp.add_mutually_exclusive_group(required=True)
    urlpm.add_argument('URL', metavar='<URL>', type=str, nargs='?', help='URL链接，传入抖音视频页面链接，未指定其它参数则默认下载该链接视频，链接举例： https://www.douyin.com/video/XXXXXX')
    # 3. 自定义参数解析与错误处理
    try:
        args = parser.parse_args()
        # 4. 检查必需参数 <URL> 是否存在（nargs="?" 使其可选，手动校验）
        if args.URL is None:
            raise argparse.ArgumentError(None, "缺少必需的 <URL> 参数")
    except argparse.ArgumentError as e:
        # 5. 捕获错误，直接打印完整帮助信息
        parser.print_help()
        # 可选：打印自定义错误提示（换行分隔，更清晰）
        print(f"\n错误：{e.message}")
        exit(1)  # 退出程序，返回非0状态码表示异常
    # 后续业务逻辑（省略）
    print(f"成功获取URL：{args.URL}")
    print(f"保存目录：{args.d if args.d else '默认目录'}")
    return parser.parse_args()


def browser_make(mute_audio=True, headless=True):
    """
    制作一个浏览器对象
    :param mute_audio: 默认静音
    :param headless: 默认隐藏界面
    :return:
    """
    # 1. 初始化Chrome选项
    option = webdriver.ChromeOptions()
    # -------------------------- 新增：指定chrome.exe的路径 --------------------------
    # 填写你的chrome.exe完整绝对路径（Windows示例，Mac/Linux请对应修改路径格式）
    chrome_exe_path = r".\chrome-win64\chrome.exe"
    # chrome_exe_path = r".\chrome-headless-shell-win64\chrome-headless-shell.exe"
    option.binary_location = chrome_exe_path  # 关键属性：指定浏览器可执行文件路径
    # --------------------------------------------------------------------------------
    # 原有配置保留不变
    if headless:
        option.add_argument('headless')  # 设置option,将窗口隐藏
    if mute_audio:
        option.add_argument("--mute-audio")  # 浏览器静音
    option.add_argument(f'--user-agent={n_agent}')  # 设置请求头的User-Agent
    option.add_argument('incognito')  # 隐身模式
    option.add_argument(
        'log-level=3')  # 禁止Python在使用chromedriver的headless模式下打印日志console信息, INFO = 0,WARNING = 1,LOG_ERROR = 2,LOG_FATAL = 3,default is 0
    option.add_argument('--start-maximized')  # 最大化运行（全屏窗口）,不设置，取元素会报错
    option.add_argument('--disable-gpu')  # 禁用GPU加速，谷歌文档提到需要加上这个属性来规避bug
    option.add_argument('--ignore-certificate-errors')  # 禁用扩展插件并实现窗口最大化
    # option.add_argument('--blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
    option.add_argument('disable-popup-blocking')  # 禁止弹窗重新加载此网站  目前不管用
    option.add_argument('disable-infobars')  # 禁用浏览器正在被自动化程序控制的提示 目前不管用
    option.add_argument('--disable-plugins')  # 禁用插件
    option.add_experimental_option('excludeSwitches', [
        'enable-logging'])  # 取消提示 DevTools listening on ws://127.0.0.1:5345/devtools/browser/e3cdda50-04a5-4a62-9da7-d3821db949cd
    # -------------------------- 新增：指定chromedriver.exe的路径 --------------------------
    # 填写你的chromedriver.exe完整绝对路径（Windows示例，Mac/Linux请对应修改路径格式，且无需.exe后缀）
    chromedriver_exe_path = r".\chromedriver.exe"
    # 2. 新增：用ChromeService封装chromedriver.exe路径（解决executable_path弃用问题）
    chrome_service = Service(executable_path=chromedriver_exe_path)  # 封装驱动路径
    # 3. 初始化浏览器：传入service参数（替代原有executable_path）
    browser = webdriver.Chrome(
        service=chrome_service,  # 传递封装好的驱动服务（Selenium 4.6.0+ 必需）
        options=option
    )
    # --------------------------------------------------------------------------------
    # 原有防检测逻辑保留不变
    # 防止检测到selenium,参考https://blog.csdn.net/cqcre/article/details/110944075
    with open(f'{sys.path[-1]}\\stealth.min.js') as f:
        js = f.read()
    browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js})
    browser.implicitly_wait(10)  # 隐性等待和显性等待可以同时用，但要注意：等待的最长时间取两者之中的大者
    browser.set_page_load_timeout(30)  # 等待30秒超时
    return browser


def mkdir(path):
    """
    目录创建函数
    :param path: 目录路径
    :return: 返回是否是否成功
    """
    path = path.strip()  # 去除首位空格
    path = path.rstrip("\\")  # 去除尾部 \ 符号
    isExists = os.path.exists(path)  # 判断路径是否存在,存在 True,不存在 False
    if not isExists:  # 判断结果,如果不存在则创建目录
        os.makedirs(path)  # 创建目录操作函数
        print("“" + path + '”目录创建成功！')
        return True
    else:  # 如果目录存在则不创建，并提示目录已存在
        print("“" + path + '”目录已存在！')
        return False


class Douyin:
    """
    获取抖音高清视频
    """

    def __init__(self, browser):
        self.browser = browser

    def VideoPageGetHomePageUrl(self,vdurl):
        self.browser.get(vdurl)
        time.sleep(1)
        hpurl_xpath = self.browser.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div/div/div[2]/div/div[1]/div[2]/a')
        hpurl = hpurl_xpath.get_attribute("href")
        return hpurl

    def album_get_pags_url(self, url):
        """
        获取专辑内全部界面链接
        :param url: 传入专辑某一视频页面
        返回
        专辑内每个视频页面链接及视频ID，{()}
        文件目录名字由用户名及专辑名构成
        :return:
        """
        self.browser.get(url)
        album_list = []
        # 点击加载更多
        print("点击加载更多")
        while True:
            try:
                ib=self.browser.find_elements(By.XPATH, "//*[@data-e2e='aweme-mix']/div[2]/button")
                for i in ib:
                    if i.accessible_name:i.click()
                if not ib: break
                print(".")
                time.sleep(3)  # 等待页面加载更多内容
            except Exception as e:  # 找不到链接则会退出循环
                print(e)
                break
        page_xpath_list = self.browser.find_elements(By.XPATH,
            "//*[starts-with(@class, 'detailPage W_')]//*[@data-e2e='aweme-mix']/ul/li/div/div[2]/h3/a")
        for page_xpath in page_xpath_list:
            page_url = page_xpath.get_attribute("href")
            video_id = re.findall(r'\d+$', page_url)[-1]  # 匹配尾部数字,取列表最后一个值
            # print((episode_txt, page_url))
            album_list.append((video_id, page_url))
        user_name = self.browser.find_element(By.XPATH,
            "//*[starts-with(@class, 'detailPage W_')]//*[@data-click-from='title']").text
        album_name = self.browser.find_element(By.XPATH,
            "//*[starts-with(@class, 'detailPage W_')]//*[@data-e2e='aweme-mix']/div/h2").text
        if not (user_name and album_name):
            print("未获取用户名及专辑名！")
            exit(3)
        file_dir_name = user_name + '/' + album_name
        return album_list, file_dir_name

    def homepage_get_pags_url(self, url):
        """
        获取主页内全部界面链接
        先加载所有页面
        :param url: 传入主页链接
        :return:
        """
        self.browser.get(url)
        print("加载页面中",end='')
        while True:
            x = self.browser.find_element(By.XPATH, '//*[@data-e2e="user-post-list"]')
            if '暂时没有更多了' in x.text:
                print("\n已经翻到底了！")
                break
            else:
                print(f'.', end="")  # 加载页面中
                # 下翻到底
                self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                time.sleep(2)  # 等待加载2秒
        all_url_list = []
        page_xpath_list = self.browser.find_elements(By.XPATH,
            '//*[@id="root"]/div/div[2]/div/div/div[4]/div[1]/div[2]/ul/li/a')
        for page_xpath in page_xpath_list:
            page_url = page_xpath.get_attribute("href")
            episode_txt = re.findall(r'\d+$', page_url)[-1]  # 匹配尾部数字,取列表最后一个值
            # print((episode_txt, page_url))
            all_url_list.append((episode_txt, page_url))
        # 抖音用户名称
        user_name = self.browser.find_element(By.XPATH,
            '//*[@id="root"]/div/div[2]/div/div/div[2]/div[1]/div[2]/h1/span/span/span/span/span').text
        return all_url_list, user_name

    def get_url(self, page_url):
        """
        获取抖音视频文件链接
        :param page_url 传入视频播放页面
        :return:
        """
        self.browser.get(page_url)
        video_xpath = self.browser.find_element(By.XPATH, '//*[@class="xg-video-container"]/video/source[3]')
        title_xpath = self.browser.find_element(By.XPATH, '//*[@id="root"]//h1')
        video_url = video_xpath.get_attribute("src")
        title = title_xpath.text
        return title, video_url

    def download_video(self, episode, page_url, file_path):
        title, video_url = self.get_url(page_url)
        agent = self.browser.execute_script("return navigator.userAgent")  # 获取当前浏览器请求头
        cookies_list = self.browser.get_cookies()  # 获取cookie名字为XSD_SESSIONID的list
        # 定义伪造访问的headers，
        headers = {
            "User-Agent": agent,
            "Cookie": f"{cookies_list[-1]['name']}={cookies_list[-1]['value']}"
        }
        # 通过视频地址下载视频
        with open(f'{file_path}/{episode}.mp4', 'wb') as fp:
            fp.write(requests.get(video_url, headers=headers).content)
        fp.close()
        with open(f"{file_path}/视频详情.csv", mode="a", encoding="utf-8") as spxx_csv:
            spxx_csv.write(f'{episode},{title},{page_url},{video_url}\n')  # 逐行存到csv文件中
        spxx_csv.close()  # 关闭文件
        # # 关闭当前视频页面
        # self.browser.close()
        # # 将页面切换到最开始的页面，视频列表页面
        # driver.switch_to.window(driver.window_handles[0])

    def auto_run(self, p_args):
        """
        自动判断链接类型，并调用程序下载视频
        :param p_args:
        :return:
        """
        if p_args.album:    # 如果为真，代表下载专辑视频
            print("正在统计专辑视频！")
            pag_url_list, file_dir_name = self.album_get_pags_url(p_args.URL)
        elif p_args.userall:   # 否则要的是用户主页链接，找到主页url,开始在主页挨个下载
            # hpgurl = self.VideoPageGetHomePageUrl(p_args.URL)
            print("正在统计主页视频！")
            pag_url_list, file_dir_name = self.homepage_get_pags_url(p_args.URL)
        else:    # 如果为真，代表下载传入的链接视频
            print("将下载单个视频！")
            self.browser.get(p_args.URL)
            now_url = self.browser.current_url
            print(now_url)
            # 一行完成：重复调用 re.findall（性能略低，兼容低版本Python）
            episode_txt = re.findall(r'\d+$', now_url)[-1] if re.findall(r'\d+$', now_url) else (print("video_id错误为空！"), "")[1]
            pag_url_list = [(episode_txt,now_url)]
            file_dir_name="单个视频"
        print(f"共计{len(pag_url_list)}个视频")
        path_dir = p_args.d + file_dir_name
        mkdir(path_dir)
        print("视频下载中.")
        m = 0
        n = 0
        for video_id, page_url in pag_url_list:
            if not os.path.exists(f"{path_dir}/{video_id}.mp4"):
                self.download_video(video_id, page_url, path_dir)
                m+=1
            else:
                n+=1
            print(f"\r已完成：{m}\t已存在：{n}\t[{m+n}\\{len(pag_url_list)}]", end='', flush=True)
        print("\n全部下载完！")
        self.browser.close()
        self.browser.quit()


if __name__ == '__main__':
    p_args = this_args()
    # print(p_args)
    # browser = browser_make(headless=False)  # 制作一个浏览器对象
    # Dy =
    Douyin(browser_make(headless=False)).auto_run(p_args)
