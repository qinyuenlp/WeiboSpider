# WeiboSpider
[![Python](https://img.shields.io/badge/Python-3.6-green.svg)](https://www.python.org/)
![selenium](https://img.shields.io/badge/selenium-3.141.0-blue.svg)  
利用`selenium`实现后台自动爬取**指定关键词下**发布的所有微博及其相关数据  
## 更新内容  
#### ▽ 2019.04.19更新
更新了用于爬取用户基本信息的程序`userSpider.py`, 并将原爬虫程序`Spider`更名为`blogSpider`。
#### ▽ 2019.01.29更新
更新了账号登录函数`weibo_login`, 更新后可以输入任意多次的验证码, 当系统不要求再次输入验证码后, ***需要在python界面中输入字符——N 程序才会继续运行***  
![example](https://github.com/QinY-Stat/WeiboSpider/blob/master/Image/%E5%BE%AE%E4%BF%A1%E5%9B%BE%E7%89%87_20190130000120.png)  
**优：能够应对任意多次验证码输入请求  
劣：无法自行判断是否需要再次输入验证码, 需要人工帮助判断**  
## 程序说明  
### 1.注意事项
1. 目前该程序只能在[Firefox](http://www.firefox.com.cn/)或[Google Chrome](https://www.google.cn/chrome)上运行, 运行程序前请确保计算机已经安装了其中一款浏览器
2. 运行程序前, 需要根据自己使用的浏览器下载对应的浏览器驱动, 并将驱动与python.exe放置在同一文件夹中, 这里给出了两种浏览器驱动的压缩文件, 也可以自行上网下载  

    浏览器名称 | 驱动名
    ---- | ----
    Firefox | geckodriver.exe
    Chrome | chromedriver.exe

### 2.爬取内容
#### 2.1 blogSpider
 内容 | 变量名 | 数据类型
 ---- | ---- | ----
  用户名 | ID | str
  用户主页 | Href | str
  微博博文 | Blog | str
  发布时间 | PubTime | str
   点赞数  | Like | int
   评论数 | Comment | int
   转发数 | Transfer | int
#### 2.2 userSpider
内容(变量名) | 数据类型 | 内容(变量名) | 数据类型
---- | ---- | ---- | ----
昵称 | str | 血型 | str
真实姓名 | str | 博客地址 | str
所在地 | str | 个性域名 | str
性别 | str | 简介 | str
性取向 | str | 注册时间 | str
感情状况 | str | href | str
生日 | str

### 3.例子
#### 3.1 blogSpider
先爬取关键词**微博**下的前20页微博信息, 接着每隔半小时(1800s)更新一次数据
```
csv_file = 'C:/test.csv'  # 数据文件保存路径
my_username = 'abcdefg'  # 微博账号
my_password = '11111111'  # 密码
keyword = '微博'  # 要搜索的关键词
my_browser = 'Chrome'  # 浏览器类型(注:仅有Firefox或Chrome两种)

Standby(keyword, csv_file, my_username, my_password, maxpage=20, sleeptime=1800, browser=my_browser)
```
#### 3.2 userSpider
可输入单个用户主页或用户主页列表(程序目前仅可识别list/array/tuple)  
主函数`userinfo`中有两个bool类型参数:`saved`、`newfile`, 分别代表是否将爬取的数据保存为csv格式数据、保存的文件是否覆盖原文件/创建新文件  
**注意: saved与newfile只要其中一个为True, 输入中都应包括filepath**
爬取单个用户主页并仅返回爬取数据:
```
myhref = 'https://weibo.com/weibokefu'
myusername = '123456'
mypassword = '123456'
only_data = userinfo(myhref, myusername, mypassword)  # 仅获取爬取的数据
```
  
爬取E:/hrefs.csv中的多个用户主页并将数据保存到C盘data文件夹中:
```
import csv

myusername = '123456'
mypassword = '123456'
myfilepath = 'C:/test.csv'
f = csv.reader(open('E:/hrefs.csv', encoding='utf-8'))
myhrefs = [href for href in f]

userinfo(myhrefs, myusername, mypassword, myfilepath, saved=True, newfilw=True)
```
