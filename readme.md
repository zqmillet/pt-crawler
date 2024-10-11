# PT-Crawler

![license](https://img.shields.io/badge/license-MIT-green)
![pytest](https://github.com/zqmillet/pt-crawler/actions/workflows/pytest.yml/badge.svg)
![pylint](https://github.com/zqmillet/pt-crawler/actions/workflows/pylint.yml/badge.svg)
![mypy](https://github.com/zqmillet/pt-crawler/actions/workflows/mypy.yml/badge.svg)
[![codecov](https://codecov.io/github/zqmillet/pt-crawler/graph/badge.svg?token=KY6EZ4Y4ER)](https://codecov.io/github/zqmillet/pt-crawler)

写这个项目, 一是自己有需求, 二是好久没写代码了, 巩固一下. 如果这个项目对你有帮助, 可以 star + fork 二连, 如果你发现一些问题或者有一些其他想法, 也欢迎提 issue.

这个以后会发到 PyPI 上的, 现在完成度太低, 暂时没上 PyPI.

现在完成了岛和馒头的相关 API, 以后会加入其他的功能, 以及兼容更多的站点.

## 安装

``` bash
pip3 install pt-crawler
```

或者 

``` bash
python3 -m pip install pt-crawler
```

## 使用

导入 `CHDBits` 类, 并进行实例化. 其他的类 API 接口与 `CHDBits` 一致.

``` python
>>> from crawlers import CHDBits

>>> headers = {'Cookie': 'your token, you can get it from browser'}

>>> chdbits = CHDBits(headers=headers)
```

调用 `get_user`, 验证权限是否正常.

``` python
>>> chdbits.get_user()
User(user_id='131177', user_name='zqmillet', upload_bytes=2958864955182416, download_bytes=2112161836957, email='zqmillet@qq.com', bonus=219185.6)
```

如果网络和权限都没问题, `get_user` 函数会返回 `User` 对象, `User` 对象包含登录用户的基本信息:

- `user_id` 代表用户的 UID.
- `user_name` 表示用户的用户名.
- `email` 表示用户注册邮箱地址.
- `upload_bytes` 表示用户上传量, 单位 Byte.
- `download_bytes` 表示用户下载量, 单位 Byte.
- `bonus` 表示用户的魔力值.
