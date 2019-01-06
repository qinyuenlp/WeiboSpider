# -*- coding: utf-8 -*-
import re
import csv
import time
import datetime
import numpy as np
from urllib import parse
from selenium import webdriver

def weibo_spider(keyword, maxpage=50, login=True, driver=None, username=None, password=None):
    ''' 执行单次爬虫 '''
    # 准备信息
    variables = ['ID', 'Href', 'Blog', 'PubTime', 'Like', 'Comment', 'Transfer']
    Weibo = {i:[] for i in variables}
    
    # 元素所在位置
    login_path = '//div[@class="gn_login"]/ul[@class="gn_login_list"]/li[3]/a[@class="S_txt1"]'
    ID_path = '//div[@class="content" and @node-type="like"]/div[1]/div[2]/a[@class="name"]'
    Blog_normal_path = '//div[@class="card-wrap" and @action-type="feed_list_item"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content"]/p[@class="txt"and @node-type="feed_list_content"]'
    Blog_extend_path = '//div[@class="card-wrap" and @action-type="feed_list_item"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content"]/p[@class="txt"and @node-type="feed_list_content_full"]'
    PubTime_path = '//div[@class="content" and @node-type="like"]/p[@class="from"]/a[@target="_blank"]'
    Like_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[4]/a'
    Comment_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[3]/a'
    Transfer_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[2]/a'
    nextpage_path = '//div[@class="m-page"]/div/a[@class="next"]'

    if login:  # 如果是第一次启动程序, 则需要执行 [打开浏览器-登录] 操作
        driver = webdriver.Firefox(executable_path='geckodriver')  # 打开浏览器
        driver.get(get_url(keyword))
        time.sleep(1)
        weibo_login(driver, login_path, username, password)  # 登录
        time.sleep(3)

    click_control = True
    current_page = 1
    while click_control and current_page <= maxpage:
        try:
            next_click = driver.find_elements_by_partial_link_text('展开全文')
            for each in next_click:  # 逐个点击'展开全文'按钮
                try:
                    each.click()
                except:
                    continue
            begin_time = datetime.datetime.now()  # 爬取数据时的时间截点
            IDs = driver.find_elements_by_xpath(ID_path)
            Blogs_normal = driver.find_elements_by_xpath(Blog_normal_path)  # 普通博文
            Blogs_extend = driver.find_elements_by_xpath(Blog_extend_path)  # 长微博博文
            PubTimes = driver.find_elements_by_xpath(PubTime_path)
            Likes = driver.find_elements_by_xpath(Like_path)
            Comments = driver.find_elements_by_xpath(Comment_path)
            Transfers = driver.find_elements_by_xpath(Transfer_path)

            Weibo['ID'] += [i.text for i in IDs]
            Weibo['Href'] += [i.get_attribute('href') for i in IDs]
            Weibo['PubTime'] += [time_process(begin_time, i.text) for i in PubTimes]  # 将时间处理为统一格式
            Weibo['Like'] += [get_number(i.text) for i in Likes]
            Weibo['Comment'] += [get_number(i.text) for i in Comments]
            Weibo['Transfer'] += [get_number(i.text) for i in Transfers]
            Blogs_list_page = [blog.text for blog in Blogs_normal]

            # 将普通博文与长微博博文合并
            extend = 0
            for i in range(len(Blogs_list_page)):
                if Blogs_list_page[i] == '':
                    Blogs_list_page[i] = Blogs_extend[extend].text
                    extend += 1
            Weibo['Blog'] += Blogs_list_page

            click_control = True
            driver.find_element_by_xpath(nextpage_path).click()  # 点击'下一页'标签, 进入下一页面
            print('######第%d页######' % current_page)
            current_page += 1
        except:
            print('爬虫结束')
            click_control = False
        
    return driver, Weibo

def get_url(keyword, page=1):
    ''' 输入关键字, 获取对应搜索界面第page页的Url, 默认从第1页开始爬取 '''
    url_mid = parse.quote(keyword)  # 将text转为URL编码
    return 'http://s.weibo.com/weibo/{mid}&page={page}'.format(mid=url_mid, page=page)

def weibo_login(driver, login_path, username=None, password=None):
    ''' 登录微博账号 '''
    driver.find_element_by_xpath(login_path).click()  # 点击'登录'按钮
    time.sleep(1)
    driver.find_element_by_name('username').clear()
    time.sleep(1)
    driver.find_element_by_name('username').send_keys(username)  # 输入微博账号
    driver.find_element_by_name('password').clear()
    driver.find_element_by_name('password').send_keys(password)  # 输入微博密码
    try:
        driver.find_element_by_class_name('W_btn_a').click()
    except:
        # 对付验证码
        driver.find_element_by_name('verifycode').clear()
        verifycode = input('VerifyCode :')
        print(verifycode)
        driver.find_element_by_name('verifycode').send_keys(verifycode)  # 输入验证码
        time.sleep(3)
        try:
            driver.find_element_by_class_name('W_btn_a').click()
        except:
            print('VerifyCode again')
            verifycode = input('VerifyCode :')
            print(verifycode)
            driver.find_element_by_name('verifycode').send_keys(verifycode)  # 再次输入验证码
            time.sleep(3)
            driver.find_element_by_class_name('W_btn_a').click()

def time_process(begintime, strtime):
    ''' 将爬取的时间统一处理为 1970-1-1 12:12 格式'''
    Y, M, D, h, m, s = re.findall(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', begintime.strftime('%Y-%m-%d %H:%M:%S'))[0]
    if re.match(r'(.*?)年(.*?)月(.*?)日 \d+:\d+', strtime):  # 匹配格式: xx年xx月xx日 xx时:xx分
        Y, M, D, h, m = re.findall(r'(\d+)年(\d+)月(\d+)日 (\d+):(\d+)', strtime)[0]
        return '%s-%s-%s %s:%s' % (Y, M, D, h, m)
    elif re.match(r'(.*?)月(.*?)日 \d+:\d+', strtime):  # 匹配格式: (今年)xx月xx日 xx时:xx分
        M, D, h, m = re.findall(r'(\d+)月(\d+)日 (\d+):(\d+)', strtime)[0]
        return '%s-%s-%s %s:%s' % (Y, M, D, h, m)
    elif re.match(r'^今天\d+:\d+', strtime):  # 匹配格式: 今天xx时:xx分
        h, m = re.findall(r'今天(\d+):(\d+)', strtime)[0]
        return '%s-%s-%s %s:%s' % (Y, M, D, h, m)
    elif re.match(r'\d+小时前$', strtime):  # 匹配格式: xx小时前
        h = re.findall(r'(\d+)小时前', strtime)[0]
        h_ago = datetime.timedelta(hours=int(h))
        return (begintime-h_ago).strftime('%Y-%m-%d %H:%M')
    elif re.match(r'(\d+)分钟前$', strtime):  # 匹配格式: xx分钟前
        m = re.findall(r'(\d+)分钟前$', strtime)[0]
        m_ago = datetime.timedelta(minutes=int(m))
        return (begintime-m_ago).strftime('%Y-%m-%d %H:%M')
    elif re.match(r'(\d+)秒前$', strtime):  # 匹配格式: xx秒前
        s = re.findall(r'(\d+)秒前', strtime)[0]
        s_ago = datetime.timedelta(seconds=int(s))
        return (begintime-s_ago).strftime('%Y-%m-%d %H:%M')

def get_number(text):
    ''' 提取数字 '''
    try:
        return int(text.split(' ')[-1])
    except:
        return 0

def select_data(Weibo, login=False, latest=None, filepath=None):
    ''' 将爬取的微博根据时间进行筛选, 只取在时间节点latest之后发布的微博 '''
    PubTime = np.array([datetime.datetime.strptime(i, '%Y-%m-%d %H:%M') for i in Weibo['PubTime']])
    if login:  # 如果是第一轮爬取, 则直接从爬取的数据中获取最近时间节点latest
        try:
            latest = latest_from_file(filepath)
            data_index = np.where(PubTime > latest)
            latest = max(PubTime)
            data = np.array(list(Weibo.values())).T[data_index]
        except:
            latest = max(PubTime)
            data = np.array(list(Weibo.values())).T
    else:  # 如果是第k轮爬取(k>1), 则先根据上一轮的latest筛选数据, 再更新latest
        data_index = np.where(PubTime > latest)
        latest = max(PubTime)
        data = np.array(list(Weibo.values())).T[data_index]
    return latest, data

def latest_from_file(filepath):
    ''' 从文件中提取最近时间 '''
    with open(filepath, encoding='utf-8') as file:
        data = np.array([row for row in csv.reader(file)]).T  # 保存的文件列名为: ID-Href-Blog-PubTime-Like-Comment-Transfer
        data_pubtime = map(lambda x:datetime.datetime.strptime(x, '%Y-%m-%d %H:%M'), data[3])
        latest = max(data_pubtime)
    return latest

def save_blog(data, filepath):
    ''' 保存数据 '''
    if re.match(r'(.*?).csv$', filepath):
        with open(filepath, 'a+', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerows(data)
            file.close()
    else:
        return ValueError('目前只支持输出csv格式')

def Standby(keyword, filepath, username=None, password=None, maxpage=50, sleeptime=3600):
    ''' 后台待机程序, 每隔一小时(3600s)更新一次数据 '''
    driver, result = weibo_spider(keyword, maxpage=maxpage, username=username, password=password)  # 第一次打开浏览器, 需要登录微博账号
    for i in result:
        print('%s:\n%d\n%s' % (i, len(result[i]), result[i]))  # 爬虫
    latest, result = select_data(result, login=True, filepath=filepath)
    save_blog(result, filepath)
    while True:
        time.sleep(sleeptime)
        driver.refresh()
        driver, result = weibo_spider(keyword, maxpage=50, login=False, driver=driver)  # 之后仅进行页面刷新以及爬取操作, 不需要登录微博账号
        latest, result = select_data(result, latest=latest)
        save_blog(result, filepath)
        print('-------------%s-------------'%latest)