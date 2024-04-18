# suanleme-copilot

遵循GPL 2.0协议

针对算了么中任务类型为“**网站服务任务**”（以下称为*长期任务*）的任务。

## 安装

```
    pip install -r requirements.txt
```

## 使用

首次运行请在本地电脑。

```
    python main.py
```

支持青龙面板（推荐），具体请参阅[whyour/qinglong](https://github.com/whyour/qinglong#%E5%86%85%E7%BD%AE%E5%91%BD%E4%BB%A4)，以下为示例：

![](https://telegraph-image.pages.dev/file/64b486f75f394981d7556.png)

## 配置与说明

首次运行会自动创建配置文件`config.json`，配置项如下：

```json
{
    "refresh_token": "",
    "pushplus_token": "pushplus token",
    "machines_remark":{
        "Machine Name": "Machine Remark"
    }
}
```

> [!NOTE]
>
> 之后的时间里，每个钟头的01分~05分内的随机时间点会重新载入一次配置文件，然后从算了么官网获取一次任务状态，并在结束时保存一次配置文件，用于更新`refresh_token`。修改配置文件时，请避开这个时间，否则容易出错。

## 功能

- [x] 监控长期任务状态

  > 如果有任务未获得积分，将发送通知；
  > 如果获得了新任务，将附加在通知里；
  > 如果有任务的状态设为“已完成”，将附加在通知里。

- [x] 监控算了么官网状态

  > 发现算了么官网服务异常时，将发送通知，
  >
  > 并在官网服务恢复时，发送一个通知。

- [x] 自动为机器备注（需要预先在配置文件中添加设备名与设备备注）

  > 当新增机器时，自动为机器添加备注，格式为「机器备注」；
  >
  > 当机器接取任务，或有任务变动时，自动为机器更新备注，格式为「机器备注 - 任务ID - 任务点ID」；
  >
  > 当失去任务点时，自动为机器更新备注，格式为「机器备注」。

## 效果

![](https://telegraph-image.pages.dev/file/e79f1845b7d297106f65f.jpg)



![](https://telegraph-image.pages.dev/file/90a99f943b3ef937e1a3d.jpg)



![](https://telegraph-image.pages.dev/file/9df673a10803331459293.jpg)


## 更新日志

- 1.1   (2024.04.18)

    优化设备备注相关代码

    优化获取积分明细相关代码

- 1.0   (2024.04.05)

    发布
