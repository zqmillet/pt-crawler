# PT-Crawler

![license](https://img.shields.io/badge/license-MIT-green)
![pytest](https://github.com/zqmillet/pt-crawler/actions/workflows/pytest.yml/badge.svg)
![pylint](https://github.com/zqmillet/pt-crawler/actions/workflows/pylint.yml/badge.svg)
![mypy](https://github.com/zqmillet/pt-crawler/actions/workflows/mypy.yml/badge.svg)
[![codecov](https://codecov.io/github/zqmillet/pt-crawler/graph/badge.svg?token=KY6EZ4Y4ER)](https://codecov.io/github/zqmillet/pt-crawler)

写这个项目, 一是自己有需求, 二是好久没写代码了, 巩固一下. 如果这个项目对你有帮助, 可以 star + fork 二连, 如果你发现一些问题或者有一些其他想法, 也欢迎提 issue.

现在完成了岛/馒头/拉面的相关 API, 以后会加入其他的功能, 以及兼容更多的站点.

该项目的初衷是为了刷流, 因此只开发了刷流相关的 API, 如果需要其他的 API, 也可以提 issue 给我.

目前 pt-crawler 支持的站点有:

| 别称 | 类                 |
|------|--------------------|
| 岛   | `crawlers.CHDBits` |
| 馒头 | `crawlers.MTeam`   |
| 拉面 | `crawlers.FSM`     |

## 安装

``` bash
pip3 install pt-crawler
```

或者 

``` bash
python3 -m pip install pt-crawler
```

## 使用

这里以岛为例, 来说明如何使用 pt-crawler. 其他的类 API 接口与 `CHDBits` 一致.

- 导入 `CHDBits` 类, 并进行实例化.
  
  ``` python
  >>> from crawlers import CHDBits
  
  >>> headers = {'Cookie': 'your cookie, you can get it from browser'}
  
  >>> chdbits = CHDBits(headers=headers)
  ```

  注意, 不同的站点, 要求的 `headers` 是不同的.
  
- 调用 `get_user`, 验证权限是否正常.
  
  ``` python
  >>> chdbits.get_user()
  User(user_id='your_id', user_name='your_name', upload_bytes=123456789, download_bytes=123456789, email='email@qq.com', bonus=233.33, passkey='****')
  ```
  
  如果网络和权限都没问题, `get_user` 函数会返回 `User` 对象, `User` 对象包含登录用户的基本信息:
  
  - `user_id` 代表用户的 UID.
  - `user_name` 表示用户的用户名.
  - `email` 表示用户注册邮箱地址.
  - `upload_bytes` 表示用户上传量, 单位 Byte.
  - `download_bytes` 表示用户下载量, 单位 Byte.
  - `bonus` 表示用户的魔力值.
  - `passkey` 表示你自己的 passkey, 这个字段是可能是 `None`, 比如馒头, 网站上不直接提供 passkey, 只能通过邮件告知 passkey, 难以通过爬虫获取.

- 调用 `get_torrents` 获取种子列表.

  ``` python
  >>> torrents = chdbits.get_torrents()
  >>> len(torrents)
  100
  >>> torrents[0]
  Torrent(torrent_id='393088', torrent_name='Le Theoreme de Marguerite 2023 1080p Bluray REMUX AVC DTS-HDMA5.1-CHD', size=31643171553, seeders=107, leechers=6, hit_and_run=259200, promotion=Promotion(upload_ratio=1.0, download_ratio=0.0), crawler=<crawlers.chdbits.CHDBits object at 0x1074bf520>)
  ```

  函数 `get_torrents` 会返回一个 `List`, 其中元素类型为 `Torrent`, `Torrent` 对象包含种子的基本信息:

  - `torrent_id` 表示种子 ID.
  - `torrent_name` 表示种子的英文名称.
  - `size` 表示种子大小, 单位 Byte.
  - `seeders` 表示种子做种人数.
  - `leechers` 表示种子下载人数.
  - `hit_and_run` 表示种子 H&R 需要保种的时间, 单位秒, 如果这个字段为 `0` 表示该种子为非 H&R 种子.
  - `promotion` 表示种子的促销策略, 它包含两个字段:
    - `upload_ratio` 表示上传促销, 比如一个种子是 2xfree, 该字段的值为 `2`.
    - `download_ratio` 表示下载促销, 比如一个种子是 50%, 该字段为 `0.5`, 如果是 free 的种子, 该字段为 `0`.

  值得一提的是 `get_torrents` 函数有一个参数 `pages` , 表示返回几页的种子, 默认值是 `1`.

  ``` python
  >>> torrents = chdbits.get_torrents(pages=3)
  >>> len(torrents)
  300
  ```

- 如果你知道种子 ID, 可以调用 `get_torrent` 函数获取某一个种子详情.

  ``` python
  >>> chdbits.get_torrent('393088')
  Torrent(torrent_id='393088', torrent_name='Le Theoreme de Marguerite 2023 1080p Bluray REMUX AVC DTS-HDMA5.1-CHD', size=31643171553, seeders=106, leechers=7, hit_and_run=259200, promotion=Promotion(upload_ratio=1.0, download_ratio=0.0), crawler=<crawlers.chdbits.CHDBits object at 0x1074bf520>)
  ```

- 下载种子有两种方式, 第一种方式是调用 `CHDBits` 类的 `download_torrent` 方法.

  ``` python
  >>> chdbits.download_torrent(torrent_id='393088', file_path='demo.torrent')
  True  
  ```

  第二种方法是调用 `Torrent` 对象的 `save` 方法.

  ``` python
  >>> torrent = chdbits.get_torrent(torrent_id='393088')
  >>> torrent.save('demo.torrent')
  True
  ```

  `CHDBits` 对象的 `download_torrent` 函数和 `Torrent` 对象的 `save` 方法在执行成功后会返回 `True`, 如果失败, 会返回 `False`.

- 查询自己活动中的任务, 可以调用 `get_tasks` 函数.

  ``` python
  >>> tasks = chdbits.get_tasks()
  >>> tasks[0]
  Task(torrent_id='393202', torrent_name='The Yangtze River 2024 2160p HQ WEB-DL H265 60fps DDP5.1-CHDWEB', status=<Status.LEECHING: 'leeching'>)
  ```

  函数 `get_tasks` 返回一个 `List`, 其中元素类型为 `Task`, `Task` 对象包含任务的基本信息:

  - `torrent_id` 表示种子的 ID.
  - `torrent_name` 表示种子的英文名称.
  - `status` 表示任务状态, `leeching` 表示正在下载, `seeding` 表示正在做种.

- 如果要使用代理访问某个站点, 可以使用 `proxy` 参数来配置代理.

  ``` python
  >>> chdbits = CHDBits(headers=headers, proxy='http://localhost:1926')
  ```

- 如果要限制访问某个站点的频率, 可以设置 `qps` 参数.

  ``` python
  >>> chdbits = CHDBits(headers=headers, qps=3)
  ```
  
  `qps = 3` 表示一秒钟最多访问 3 次, 如果你没设置 `qps` 参数, 那么则不会限制频率, 会短时间激增网站负载, 容易被封.

- 如果一个站有多个域名, 你可以通过 `base_url` 参数来修改默认值.

  ``` python
  >>> chdbits = CHDBits(headers=headers, base_url='https://hello.world')
  ```

  注意: `base_url` 不要以 `/` 结尾.

- 你可以为 `CHDBits` 指定一个日志对象, 这样 `CHDBits` 在运行的过程中, 会把异常信息输出到日志中.

  ``` python
  >>> from loguru import logger
  >>> chdbits = CHDBits(headers=headers, logger=logger)
  ```

## 开发

### 添加新的爬虫类

在 `crawlers` 文件夹中新建一个爬虫类文件. 在该文件中实现爬虫类, 该爬虫类必须继承 `crawlers.base.Crawler` 类, 并实现其所有抽象方法.

在 `crawlers/__init__.py` 文件中引入你新建的爬虫类, 方便其他人导入.

### 编写测试用例

本工程使用的自动化测试框架为 pytest.

在 `testcases` 文件夹中新建对应的爬虫类的单元测试, 并实现所有抽象方法的测试用例.

### 执行测试用例

首先运行 `pip3 install -r testcases/requirements.txt` 来安装运行测试必要的库, 然后执行以下命令来执行用例.

``` bash
$ pytest [--proxy <proxy>] --cov crawlers testcases
```

其中 `--proxy` 为可选参数, 如果需要通过代理访问站点, 请添加代理. 目前代理只支持 HTTP 和 HTTPS 两种类型.

### 静态检查

提交前请使用 mypy 和 pylint 对工程进行静态检查, 如果有任何静态问题, 请在提交前修复, 本项目对静态缺陷零容忍.

``` bash
$ mypy crawlers
Success: no issues found in 7 source files
```

``` bash
$ pylint crawlers
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```

该项目也配置了 CI/CD, 每次提交都会自动执行所有测试用例以及静态检查.
