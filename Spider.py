# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 13:27:40 2018

@author: Administrator
"""
import time
import xlrd,xlwt
import os
from urllib import parse
from selenium import webdriver
from xlutils.copy import copy
import jieba
import WordCloud as WC
import gensim
import re
import csv
import numpy as np
import datetime

def weibo_spider(text, maxpage=50, login=True, driver=None, username=None, password=None):
    # 准备信息
    variables = ['ID', 'Href', 'Blog', 'PubTime', 'Like', 'Comment', 'Transfer']
    Weibo = {i:[] for i in variables}

    login_path = '//div[@class="gn_login"]/ul[@class="gn_login_list"]/li[3]/a[@class="S_txt1"]'
    ID_path = '//div[@class="content" and @node-type="like"]/div[1]/div[2]/a[@class="name"]'
    Blog_normal_path = '//div[@class="card-wrap" and @action-type="feed_list_item"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content"]/p[@class="txt"and @node-type="feed_list_content"]'
    Blog_extend_path = '//div[@class="card-wrap" and @action-type="feed_list_item"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content"]/p[@class="txt"and @node-type="feed_list_content_full"]'
    Tool_path = '//div[@class="content" and @node-type="like"]/p[@class="from"]/a[@rel="nofollow"]'
    Like_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[4]/a'
    Comment_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[3]/a'
    Transfer_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[2]/a'

    if login:  # 如果是第一次启动程序, 则需要执行 [打开浏览器-登录] 操作
        driver = webdriver.Firefox(executable_path='geckodriver')  # 打开浏览器
        driver.get(get_url(text))
        time.sleep(1)
        weibo_login(driver, login_path, username, password)  # 登录
        time.sleep(3)

    click_control = True
    current_page = 1
    while click_control and current_page <= maxpage:
        next_click = driver.find_elements_by_partial_link_text('展开全文')
        for each in next_click:
            each.click()
            time.sleep(0.1)
        begin_time = datetime.datetime.now()  # 爬取数据时的时间截点
        IDs = driver.find_elements_by_xpath(ID_path)
        Blogs_normal = driver.find_elements_by_xpath(Blog_normal_path)
        Blogs_extend = driver.find_elements_by_xpath(Blog_extend_path)
        PubTimes = driver.find_elements_by_xpath(PubTime_path)
        Likes = driver.find_elements_by_xpath(Like_path)
        Comments = driver.find_elements_by_xpath(Comment_path)
        Transfers = driver.find_elements_by_xpath(Transfer_path)

        Weibo['ID'] += [i.text for i in IDs]
        Weibo['Href'] += [i.get_attribute('href') for i in IDs]
        Weibo['PubTime'] += [time_process(begin_time, i.text) for i in PubTimes]
        Weibo['Like'] += [get_number(i.text) for i in Likes]
        Weibo['Comment'] += [get_number(i.text) for i in Comments]
        Weibo['Transfer'] += [get_number(i.text) for i in Transfers]
        Blogs_list_page = [blog.text for blog in Blogs_normal]

        extend = 0
        for i in range(len(Blogs_list_page)):
            if Blogs_list_page[i] == '':
                Blogs_list_page[i] = Blogs_extend[extend].text
                extend += 1
        Weibo['Blog'] += Blogs_list_page

        click_control = True
        driver.find_element_by_partial_link_text('下一页').click()
        print('######第%d页######' % current_page)
        current_page += 1
        # except:
        #     print('爬虫结束')
        #     click_control = False
    return driver, Weibo

def get_url(keyword, page=1):
    # 输入关键字, 获取对应搜索界面第page页的Url, 默认从第1页开始爬取
    url_mid = parse.quote(keyword)  # 将text转为URL编码
    return 'http://s.weibo.com/weibo/{mid}&page={page}'.format(mid=url_mid, page=page)

def weibo_login(driver, login_path, username=None, password=None):
    driver.find_element_by_xpath(login_path).click()  # 点击'登录'按钮
    time.sleep(1)
    driver.find_element_by_name('username').clear()
    time.sleep(1)
    driver.find_element_by_name('username').send_keys(username)  # 输入微博账号
    driver.find_element_by_name('password').clear()
    driver.find_element_by_name('password').send_keys(password)  # 输入微博密码
    # driver.find_element_by_class_name('W_btn_a').click()
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
    Y, M, D, h, m, s = re.findall(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', begintime.strftime('%Y-%m-%d %H:%M:%S'))[0]
    if re.match(r'(.*?)年(.*?)月(.*?)日 \d+:\d+', strtime):
        Y, M, D, h, m = re.findall(r'(\d+)年(\d+)月(\d+)日 (\d+):(\d+)', strtime)[0]
        return '%s-%s-%s %s:%s' % (Y, M, D, h, m)
    elif re.match(r'(.*?)月(.*?)日 \d+:\d+', strtime):
        M, D, h, m = re.findall(r'(\d+)月(\d+)日 (\d+):(\d+)', strtime)[0]
        return '%s-%s-%s %s:%s' % (Y, M, D, h, m)
    elif re.match(r'^今天\d+:\d+', strtime):
        h, m = re.findall(r'今天(\d+):(\d+)', strtime)[0]
        return '%s-%s-%s %s:%s' % (Y, M, D, h, m)
    elif re.match(r'\d+小时前$', strtime):
        h = re.findall(r'(\d+)小时前', strtime)[0]
        h_ago = datetime.timedelta(hours=int(h))
        return (begintime-h_ago).strftime('%Y-%m-%d %H:%M')
    elif re.match(r'(\d+)分钟前$', strtime):
        m = re.findall(r'(\d+)分钟前$', strtime)[0]
        m_ago = datetime.timedelta(minutes=int(m))
        return (begintime-m_ago).strftime('%Y-%m-%d %H:%M')
    elif re.match(r'(\d+)秒前$', strtime):
        s = re.findall(r'(\d+)秒前', strtime)[0]
        s_ago = datetime.timedelta(seconds=int(s))
        return (begintime-s_ago).strftime('%Y-%m-%d %H:%M')

def get_number(text):
    try:
        return int(text.split(' ')[-1])
    except:
        return 0

def select_data(Weibo, login=False, latest=None):
    PubTime = np.array([datetime.datetime.strptime(i, '%Y-%m-%d %H:%M') for i in Weibo['PubTime']])
    if login:
        latest = max(PubTime)
        data = np.array(list(Weibo.values())).T
    else:
        data_index = np.where(PubTime > latest)
        latest = max(PubTime)
        data = np.array(list(Weibo.values())).T[data_index]
    return latest, data

def save_blog(data, filepath):
    if re.match(r'(.*?).csv$', filepath):
        with open(filepath, 'a+', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerows(data)
            file.close()
    else:
        return ValueError('目前只支持输出csv格式')

def Standby(keyword, filepath, maxpage=50, sleeptime=3600):
    driver, result = weibo_spider(keyword, maxpage=50)
    for i in result:
        print('%s:\n%d\n%s' % (i, len(result[i]), result[i]))  # 爬虫
    latest, result = select_data(result, login=True)
    save_blog(result, filepath)
    while True:
        time.sleep(sleeptime)
        driver.refresh()
        driver, result = weibo_spider(keyword, maxpage, False, driver)
        latest, result = select_data(result, latest=latest)
        save_blog(result, filepath)
