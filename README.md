# WeiboSpider
利用`selenium`实现后台自动爬取**指定关键词下**发布的所有微博及其相关数据
## 爬取内容

 内容 | 变量名 | 数据类型
 ---- | ---- | ----
  用户名 | ID | str
  用户主页 | Href | str
  微博博文 | Blog | str
  发布时间 | PubTime | str
   点赞数  | Like | int
   评论数 | Comment | int
   转发数 | Transfer | int

## 例子
先爬取关键词**微博**下的前20页微博信息, 接着每隔半小时(1800s)更新一次数据
```
csv_file = 'C:/test.csv'
my_username = 'abcdefg'
my_password = '11111111'
keyword = '微博'

Standby(keyword, csv_file, my_username, my_password, maxpage=20, sleeptime=1800)
