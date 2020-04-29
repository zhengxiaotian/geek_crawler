# geek_crawler

最近极客时间有个活动，企业可以为每位员工免费领取3门课程。刚好我们公司领导也给我们申请了这个权益（没有领取的可以找领导说说帮忙弄一下，[活动地址](https://account.geekbang.org/biz/signin?redirect=https%3A%2F%2Fservice.geekbang.org%2Fdashboard%2Fhome%2F%3Futm_source%3Dfrontshow%26utm_medium%3Dwechat%26utm_campaign%3D316%26utm_term%3Dfrontend%26gk_source%3Dfrontshowwechat&gk_source=frontshowwechat&utm_source=frontshow&utm_medium=wechat&utm_campaign=316&utm_term=frontend)）。

免费领取的课程只有30天有效期，因为工作日白天要正常上班，30天之内没法学完3门课程。所以就写了个脚本，将账号下所有可以看到的专栏课程自动保存到本地。

### :boom: 该项目仅限学习交流使用，请勿用于任何商业行为和损害其它人利益的行为。 :boom:

### 如何使用

1. 将代码 clone 到本地

   ```shell
   git clone git@github.com:zhengxiaotian/geek_crawler.git
   ```

2. 直接在终端或者 Pycharm 中运行脚本(ps: 代码是在 Python3 下编写的，需要使用 Python3 运行)

   ```shell
   python geek_crawler.py
   ```

3. 输入账号密码

   ```shell
   E:\geek_crawler (master -> origin)
   λ python geek_crawler.py
   请输入你的极客时间账号（手机号）: *************
   请输入你的极客时间密码: ************
   ```

4. 抓取完成

   ```shell
   2020-04-28 19:32:41,624 - geek_crawler.py[line:307] - INFO: 请求获取文章信息接口：
   2020-04-28 19:32:41,633 - geek_crawler.py[line:320] - INFO: 接口请求参数：{'id': 225554, 'include_neighbors': 'tru
   e', 'is_freelyread': 'true'}
   2020-04-28 19:32:42,047 - geek_crawler.py[line:349] - INFO: ----------------------------------------
   2020-04-28 19:32:47,131 - geek_crawler.py[line:478] - INFO: 正常抓取完成。
   ```

   ![Snipaste_2020-04-29_08-55-08.png](http://ww1.sinaimg.cn/large/655c061fgy1geacsajgz4j20pk04lmxq.jpg)

   *PS：如果抓取过程中有接口报错导致抓取中断，可以查看日志中对应的报错信息，然后直接重新跑脚本继续抓取（之前抓取成功的文章会在本地有文档记录，后续不会重复抓取的）*

   

### 成果展示

![Snipaste_2020-04-29_08-44-44.png](http://ww1.sinaimg.cn/large/655c061fgy1geacmd7a5fj20nq035mxa.jpg)

![Snipaste_2020-04-28_19-31-52.png](http://ww1.sinaimg.cn/large/655c061fgy1ge9plld31oj20nd0h6gqf.jpg)



### 功能清单

- [x] 输入账号密码后自动将该账号下所有可以看到的专栏（图文+音频），保存到本地；

- [x] 可以支持选择保存成 Markdown 文档或者 HTML 文档；

- [x] 支持配置排除某些课程的拉取（比如已经有的课程不再下载）；

- [ ] 抓取指定名称的课程；

- [ ] 将每篇文章的评论与正文一起保存到本地；

- [ ] 将视频拉取下来保存成 MP4 文件；

  
