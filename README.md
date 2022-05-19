## nonebot-plugin-imageutils


### 功能

- 提供 `BuildImage` 类，方便图片尺寸修改、添加文字等操作
- 提供 `Text2Image` 类，方便实现文字转图，支持少量 `BBCode` 标签
- 文字支持多种字体切换，能够支持 `emoji`
- 添加文字自动调节字体大小


### 安装

- 使用 nb-cli

```
nb plugin install nonebot_plugin_imageutils
```

- 使用 pip

```
pip install nonebot_plugin_imageutils
```


### 配置字体

本插件选择了一些不同系统上的字体，以支持更多的字符

对于 `Ubuntu` 系统，建议安装 `fonts-noto` 软件包 以支持中文字体和 emoji

默认备选字体列表可在 `nonebot_plugin_imageutils/config.py` 中查看

可在 `.env` 文件中添加相应的变量来自定义备选字体

字体文件需要在系统目录下，或放置于机器人运行目录下的 `data/fonts/` 文件夹中

其他插件可以通过 `nonebot_plugin_imageutils/fonts.py` 中的 `add_font` 函数往字体文件夹中添加字体


### 使用示例


- `BuildImage`

```python
from nonebot_plugin_imageutils import BuildImage

# output: BytesIO
output = BuildImage.new((300, 300)).circle().draw_text((30, 30, 270, 270), "测试ymddl😂").save_jpg()
```

![1.jpg](https://s2.loli.net/2022/05/19/gFdpwWPCzreb2X6.jpg)


- `Text2Image`

```python
from nonebot_plugin_imageutils import Text2Image

# img: PIL.Image.Image
img = Text2Image.from_text("@mnixry 🤗", 50).to_image()
```

![2.png](https://s2.loli.net/2022/05/19/14EXViZQwcGUW5I.png)


- 使用 `BBCode`

```python
from nonebot_plugin_imageutils import text2image

# img: PIL.Image.Image
img = text2image("N[size=40][color=red]o[/color][/size]neBo[size=30][color=blue]T[/color][/size]\n[align=center]太强啦[/align]")
```

![3.png](https://s2.loli.net/2022/05/19/VZAXsKB2x65q7rl.png)


### 特别感谢

- [HibiKier/zhenxun_bot](https://github.com/HibiKier/zhenxun_bot) 基于 Nonebot2 和 go-cqhttp 开发，以 postgresql 作为数据库，非常可爱的绪山真寻bot
