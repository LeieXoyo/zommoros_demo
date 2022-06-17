# zommoros
自主开发的量化回测实盘交易程序.
回测框架采用了backtrader.
数据库采用了mysql和sqlite(ORM采用orator).
交易所api采用了ccxt和binance restapi.
信号接收模块采用了flask建立webhook服务端, 接收并处理来自tradingview的信号.
警报模块采用了邮件提醒和钉钉群聊机器人提醒的方式.

项目请求:
  需要币安、欧易其中至少一个的交易apikey.
  如需邮件提醒则要提供smtp凭据, 钉钉群聊机器人提醒需要提供webhook地址.
