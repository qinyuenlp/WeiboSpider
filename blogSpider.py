# -*- coding: utf-8 -*-
import re
import csv
import time
import datetime
import numpy as np
from urllib import parse
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def weibo_spider(keyword, maxpage=50, login=True, driver=None, username=None, password=None, browser='Firefox',
                 scope=None, time_from=None, time_to=None):
    '''
    执行单次爬虫
    Parameter
    --------
    keyword: 要爬取的关键词
    maxpage: 需要爬取多少页
    login: 是否需要登录
    driver: 浏览器驱动, 若仅爬取一次或第一次爬取, 则该参数取None即可; 若需要自动爬取多次, driver=第一次爬取时定义的驱动参数名
    username: 微博账号
    password: 微博密码
    browser: 浏览器类型, 只能取['Firefox', 'Chrome']中的其中一个
    scope: 搜索结果的范围, 目前仅支持"all"或"origin"
    time_from: 按时间查询, 起始日期, 例: 2019-05-01
    time_to: 按时间查询, 结束日期, 例: 2019-05-07

    Return
    --------
    driver: WebDriver
        浏览器状态
    Weibo: dict
        爬取的数据
    '''
    # 准备信息
    variables = ['ID', 'Href', 'Blog', 'PubTime', 'Like', 'Comment', 'Transfer']
    Weibo = {i: [] for i in variables}
    if scope and scope not in ["all", "origin"]:
        raise ValueError("参数'scope'必须为None或'all'或'origin'.")

    if time_from and time_to:
        url = get_url(keyword, time_from=time_from, time_to=time_to, scope=scope)
    elif time_from == time_to == None:
        url = get_url(keyword, page=1, scope=scope)
    else:
        raise ValueError("参数'time_from'与'time_to'应当同时有值或同时无值.")

    if login:  # 如果是第一次启动程序, 则需要执行 [打开浏览器-登录] 操作
        if browser == 'Firefox':
            driver = webdriver.Firefox(executable_path='geckodriver')  # 打开浏览器
        elif browser == 'Chrome':
            driver = webdriver.Chrome(executable_path='chromedriver')
        else:
            return ValueError("目前仅支持Firefox与Chrome浏览器.")
        driver.get(url)
        time.sleep(2)
        try:
            weibo_login(driver, username, password)  # 登录
        except TimeoutException:
            driver.quit()
            weibo_spider(keyword, maxpage, login, driver, username, password, browser, scope, time_from, time_to)
        time.sleep(3)
    driver.get(url)
    click_control = True
    current_page = 1
    while click_control and current_page <= maxpage:
        driver.set_page_load_timeout(10)
        try:
            Weibo = get_blog(driver, Weibo)  # 爬取并更新结果
            to_nextpage(driver)

            print('######第%d页######' % current_page)
            current_page += 1
        except TimeoutError:
            driver.refresh()
        except:
            print('爬虫结束')
            click_control = False
            driver.get(url)

    return driver, Weibo

def get_blog(driver, Weibo):
    ID_path = '//div[@class="card-wrap"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content" and @node-type="like"]/div[@class="info"]/div[2]/a[1]'
    Blog_normal_path = '//div[@class="card-wrap"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content" and @node-type="like"]/p[@class="txt"and @node-type="feed_list_content"]'
    Blog_extend_path = '//div[@class="card-wrap"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content" and @node-type="like"]/p[@class="txt"and @node-type="feed_list_content_full"]'
    PubTime_path = '//div[@class="card-wrap"]/div[@class="card"]/div[@class="card-feed"]/div[@class="content" and @node-type="like"]/p[@class="from"]/a[1]'
    Like_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[4]/a'
    Comment_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[3]/a'
    Transfer_path = '//div[@class="card"]/div[@class="card-act"]/ul/li[2]/a'

    next_click = driver.find_elements_by_partial_link_text('展开全文')
    for each in next_click:  # 逐个点击'展开全文'按钮
        try:
            each.click()
        except:
            continue
    time.sleep(1)
    begin_time = datetime.datetime.now()  # 爬取数据时的时间截点
    IDs = driver.find_elements_by_xpath(ID_path)
    time.sleep(0.1)
    Blogs_normal = driver.find_elements_by_xpath(Blog_normal_path)  # 普通博文
    time.sleep(0.1)
    Blogs_extend = driver.find_elements_by_xpath(Blog_extend_path)  # 长微博博文
    time.sleep(0.1)
    PubTimes = driver.find_elements_by_xpath(PubTime_path)
    time.sleep(0.1)
    Likes = driver.find_elements_by_xpath(Like_path)
    time.sleep(0.1)
    Comments = driver.find_elements_by_xpath(Comment_path)
    time.sleep(0.1)
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
            try:
                Blogs_list_page[i] = Blogs_extend[extend].text
                extend += 1
            except:
                continue
    Weibo['Blog'] += Blogs_list_page

    return Weibo

def to_nextpage(driver):
    nextpage_path = '//div[@class="m-page"]/div/a[@class="next"]'
    try:
        driver.find_element_by_xpath(nextpage_path).click()  # 点击'下一页'标签, 进入下一页面
    except:
        driver.refresh()
        driver.find_element_by_xpath(nextpage_path).click()

def get_url(keyword, page=None, time_from=None, time_to=None, scope=None):
    ''' 输入关键字, 获取对应搜索界面第page页的Url, 默认从第1页开始爬取 '''
    url_mid = parse.quote(keyword)  # 将text转为URL编码
    if page:
        if not scope:
            return 'http://s.weibo.com/weibo/{mid}&page={page}'.format(mid=url_mid, page=page)
        elif scope == "all":
            return 'http://s.weibo.com/weibo/{mid}&page={page}&nodup=1'.format(mid=url_mid, page=page)
        elif scope == "origin":
            return 'http://s.weibo.com/weibo/{mid}&scope={scope}&page={page}'.format(mid=url_mid, scope='ori', page=page)
    elif time_from and time_to:
        if scope == "origin":
            return 'http://s.weibo.com/weibo/{mid}&scope={scope}&timescope=custom:{timefrom}:{timeto}'.format(mid=url_mid, scope='ori', timefrom=time_from, timeto=time_to)
        else:
            return 'http://s.weibo.com/weibo/{mid}&timescope=custom:{timefrom}:{timeto}'.format(mid=url_mid, timefrom=time_from, timeto=time_to)

def weibo_login(driver, username, password):
    ''' 执行登录操作 '''
    login_path = '//div[@class="gn_login"]/ul[@class="gn_login_list"]/li[3]/a[@class="S_txt1"]'
    username_path = '/html/body/div[@node-type="outer"]/div[2]/div[3]/div[3]/div[@node-type="username_box"]/input'
    password_path = '/html/body/div[@node-type="outer"]/div[2]/div[3]/div[3]/div[@node-type="password_box"]/input'

    driver.find_element_by_xpath(login_path).click()  # 点击'登录'按钮
    # time.sleep(2)
    WebDriverWait(driver, 5, 0.5).until(EC.presence_of_element_located((By.XPATH, username_path)))
    driver.find_element_by_xpath(username_path).clear()
    driver.find_element_by_xpath(username_path).send_keys(username)  # 输入微博账号
    driver.find_element_by_xpath(password_path).clear()
    driver.find_element_by_xpath(password_path).send_keys(password)  # 输入微博密码
    login_verifycode(driver)

def login_verifycode(driver):
    ''' 执行登录中对验证码的所有操作 '''
    verifycode_path = '/html/body/div[@node-type="outer"]/div[@class="content"]/div[@node-type="inner"]/div[@node-type="login_frame"]/div[@class="item verify"]/input'
    login_path = '/html/body/div[@node-type="outer"]/div[@class="content"]/div[@node-type="inner"]/div[@node-type="login_frame"]/div[@class="item_btn"]/a'
    driver.find_element_by_xpath(login_path).click()
    time.sleep(1)
    try:
        driver.find_element_by_xpath(verifycode_path).click()
        need_verifycode = True
        while need_verifycode:
            need_verifycode = login_verifycode_input(driver, login_path)
    except:
        pass

def login_verifycode_input(driver, login_path):
    ''' 输入验证码 '''
    verifycode_path = '/html/body/div[@node-type="outer"]/div[@class="content"]/div[@node-type="inner"]/div[@node-type="login_frame"]/div[@class="item verify"]/input'

    verifycode = input('VerifyCode :')
    if verifycode == 'N':
        return False
    else:
        print(verifycode)
        driver.find_element_by_xpath(verifycode_path).send_keys(verifycode)  # 输入验证码
        driver.find_element_by_xpath(login_path).click()
        return True

def time_process(begintime, strtime_input):
    ''' 将爬取的时间统一处理为 1970-1-1 12:12 格式'''
    strtime_list = strtime_input.split(' ')
    if re.match(r'^转赞*.?', strtime_list[-1]):  # 能成功匹配到该字符串 则一定有len(strtime_list) >= 2
        del(strtime_list[-1])
        if strtime_list[0] == '今天':
            strtime = ''.join(strtime_list)
        else:
            strtime = ' '.join(strtime_list)
    else:
        strtime = strtime_input
    Y, M, D, h, m, s = re.findall(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', begintime.strftime('%Y-%m-%d %H:%M:%S'))[0]
    if re.match(r'(\d+)-(\d+)-(\d+) (\d+):(\d+)', strtime):
        return strtime
    elif re.match(r'(.*?)年(.*?)月(.*?)日 \d+:\d+', strtime):  # 匹配格式: xx年xx月xx日 xx时:xx分
        Y, M, D, h, m = re.findall(r'(\d+)年(\d+)月(\d+)日 (\d+):(\d+)', strtime)[0]
        return '%s-%s-%s %s:%s' % (Y, M, D, h, m)
    elif re.match(r'(.*?)月(.*?)日 \d+:\d+', strtime):  # 匹配格式: (今年)xx月xx日 xx时:xx分
        M, D, h, m = re.findall(r'(\d+)月(\d+)日 (\d+):(\d+)', strtime)[0]
        return '%s-%s-%s %s:%s' % (Y, M, D, h, m)
    elif re.match(r'^今天', strtime):  # 匹配格式: 今天xx时:xx分
        if len(strtime.split(' ')) == 1:
            strtime = ''.join(strtime_list)
        else:
            strtime = ' '.join(strtime_list)
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

def Standby(keyword, filepath, username=None, password=None, maxpage=50, sleeptime=3600, browser='Firefox', scope=None):
    '''
    后台待机程序, 每隔一小时(3600s)更新一次数据
    sleeptime: 两次爬取操作的时间间隔, 单位为秒(s)
    scope: 搜索结果的范围, 目前仅支持"all"或"origin"
    '''
    driver, result = weibo_spider(keyword, maxpage=maxpage, username=username, password=password, browser=browser, scope=scope)  # 第一次打开浏览器, 需要登录微博账号
    for i in result:
        print('%s:\n%d\n%s' % (i, len(result[i]), result[i]))  # 爬虫
    latest, result = select_data(result, login=True, filepath=filepath)
    save_blog(result, filepath)
    while True:
        time.sleep(sleeptime)
        driver.refresh()
        driver, result = weibo_spider(keyword, maxpage=50, login=False, driver=driver, browser=browser, scope=scope)  # 之后仅进行页面刷新以及爬取操作, 不需要登录微博账号
        latest, result = select_data(result, latest=latest)
        save_blog(result, filepath)
        print('-------------%s-------------'%latest)

if __name__ == '__main__':
    csv_file = 'C:/test.csv'
    my_username = 'myusername'
    my_password = 'mypassword'
    keyword = '微博'
    my_browser = 'Firefox'  # 'Firefox'/'Chrome'
    scope = 'origin'  # None/'all'/'origin'
    
    # 待机爬取示例
    Standby(keyword, csv_file, my_username, my_password, maxpage=50, sleeptime=1800, browser=my_browser, scope=scope)
    
    # # 按指定时间段爬取示例(2019年5月1日06:00至2019年5月7日23:00的搜索结果)
    # time_start = '2019-05-01-06'
    # time_end = '2019-05-07-23'
    # driver, weibo_result = weibo_spider(keyword=keyword, username=my_username, password=my_password, time_from=time_start, time_to=time_end, scope=scope)
    # latest, result = select_data(weibo_result, login=True, filepath=csv_file)
    # save_blog(result, csv_file)
    # print(weibo_result)
