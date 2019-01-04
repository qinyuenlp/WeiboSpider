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

def weibo_spider(text, maxpage=50, login=True, driver=None):

    # 准备信息
    click_control = True
    current_page = 1
    variables = ['ID', 'Href', 'Blog', 'PubTime', 'Like', 'Comment', 'Transfer']
    Weibo = {i:[] for i in variables}

    login_path = '//div[@class="gn_login"]/ul[@class="gn_login_list"]/li[3]/a[@class="S_txt1"]'
    ID_path = '//div[@class="content" and @node-type="like"]/div[1]/div[2]/a[@class="name"]'
    Blog_normal_path = '//div[@class="card-wrap" and @action-type="feed_list_item"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content"]/p[@class="txt"and @node-type="feed_list_content"]'
    Blog_extend_path = '//div[@class="card-wrap" and @action-type="feed_list_item"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content"]/p[@class="txt"and @node-type="feed_list_content_full"]'
    PubTime_path = '//div[@class="content" and @node-type="like"]/p[@class="from"]/a[@target="_blank"]'
    Position_path = ''
    Tool_path = '//div[@class="content" and @node-type="like"]/p[@class="from"]/a[@rel="nofollow"]'
    Like_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[4]/a'
    Comment_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[3]/a'
    Transfer_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[2]/a'

    if login:  # 如果是第一次启动程序, 则需要执行 [打开浏览器-登录] 操作
        driver = webdriver.Firefox(executable_path='geckodriver')  # 打开浏览器
        driver.get(get_url(text))
        time.sleep(1)
        weibo_login(driver, login_path)  # 登录
        time.sleep(3)

    while click_control and current_page <= maxpage:
        # try:
        next_click = driver.find_elements_by_partial_link_text('展开全文')
        for each in next_click:
            each.click()
            time.sleep(0.1)
        begin_time = datetime.datetime.now()  # 爬取数据时的时间截点
        IDs = driver.find_elements_by_xpath(ID_path)
        Blogs_normal = driver.find_elements_by_xpath(Blog_normal_path)
        Blogs_extend = driver.find_elements_by_xpath(Blog_extend_path)
        PubTimes = driver.find_elements_by_xpath(PubTime_path)
        Positions = None
        Tools = None
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

def userinfo_spider():
    pass

def get_url(keyword, page=1):
    # 输入关键字, 获取对应搜索界面第page页的Url, 默认从第1页开始爬取
    url_mid = parse.quote(keyword)  # 将text转为URL编码
    return 'http://s.weibo.com/weibo/{mid}&page={page}'.format(mid=url_mid, page=page)

def weibo_login(driver, login_path):
    driver.find_element_by_xpath(login_path).click()  # 点击'登录'按钮
    time.sleep(1)
    driver.find_element_by_name('username').clear()
    time.sleep(1)
    driver.find_element_by_name('username').send_keys('981090870@qq.com')  # 输入微博账号
    driver.find_element_by_name('password').clear()
    driver.find_element_by_name('password').send_keys('xa13978289766')  # 输入微博密码
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

    # elif re.match(r'(.*?).txt$', filepath):
    #     with open(filepath, 'a+', encoding='utf-8') as file:
    #         for each in zip(data['ID'], data['Href'], data['Blog'], data['PubTime']):
    #             user, user_href, blog, blog_time = each
    #             if each[0] != '':
    #                 # f.write(comment)
    #                 # f.write('\n######\n')
    #                 file.write('ID: %s\nhref: %s\nblog: %s\ntime: %s' % (user, user_href, blog, blog_time))
    #                 # f.write('blog: %s\n'%comment)
    #                 # f.write('\n######\n')
    #         file.close()
    else:
        return ValueError('目前只支持输出csv格式')

def save_user():
    pass

def get_topics(txt_file, temp=[], num_topics=2, num_words=10):
    texts = []  # 读取文本, 筛选掉空文本和爬虫时设置的文本之间的分隔符:'######'
    with open(txt_file, 'r', encoding='utf-8') as a:
        for each in a:
            if re.match(r'^blog:', each) and not re.match(r'^ ', each) and not re.match('######', each):
                texts.append(each)

    corpus = []  # 分词, 并排除''
    for text in texts:
        words = WC.seg_sentence(text, WC.stopwords_path, temp).split(' ')
        words2add = []
        for word in words:
            if word not in  ['', 'blog']:
                words2add.append(word)
        corpus.append(words2add)

    dictionary = gensim.corpora.Dictionary(corpus)
    corpus = [dictionary.doc2bow(text) for text in corpus]
    ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=num_topics, id2word=dictionary)
    return ldamodel.print_topics(num_words=num_words)

def Standby(keyword, filepath, maxpage=50, sleeptime=3600):
    turn = 1
    driver, result = weibo_spider(keyword, maxpage=50)
    for i in result:
        print('%s:\n%d\n%s' % (i, len(result[i]), result[i]))  # 爬虫
    latest, result = select_data(result, login=True)
    save_blog(result, filepath)
    while turn > 2:
        time.sleep(sleeptime)
        driver.refresh()
        driver, result = weibo_spider(keyword, maxpage, False, driver)
        latest, result = select_data(result, latest=latest)
        save_blog(result, filepath)
        turn += 1

if __name__ == '__main__':
    txt_file = 'D:/Codes/Py_Codes/爬虫/支付宝/支付宝_20181227_1704.txt'  # 文本——存放路径
    csv_file = 'D:/Codes/Py_Codes/爬虫/支付宝/网易云年度总结_20190103.csv'  # 文本——存放路径
    jpg_file = 'D:/Codes/Py_Codes/爬虫/支付宝/支付宝_20181227_1704.jpg'  # 词云——图存放路径
    mask = 'D:/Codes/Py_Codes/爬虫/QQ.jpg'  # 词云——背景图片路径
    temp = ['', '支付宝', '微信', '收起', '全文', '网页', '链接', '首页', '\n', 'blog']  # 文本+词云——不希望出现在词云与LDA中的词

    Standby('网易云年度总结', filepath=csv_file, maxpage=1, sleeptime=5)

    # WC.build_wordcloud(txt_file, save_path=jpg_file, mask=mask, temp=temp)  # 词云
    # topics = get_topics(txt_file, temp, num_topics=2, num_words=10)
    # for i in range(len(topics)):
    #     print('主题%d: %s'%(i+1, topics[i]))
    #
    
    
    
    
    
    

