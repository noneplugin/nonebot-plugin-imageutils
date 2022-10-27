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

> 对于 `Ubuntu` 系统，建议安装 `fonts-noto` 软件包 以支持中文字体和 emoji
>
> 并将简体中文设置为默认语言：（否则会有部分中文显示为异体（日文）字形，详见 [ArchWiki](https://wiki.archlinux.org/title/Localization_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)/Simplified_Chinese_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)#%E4%BF%AE%E6%AD%A3%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87%E6%98%BE%E7%A4%BA%E4%B8%BA%E5%BC%82%E4%BD%93%EF%BC%88%E6%97%A5%E6%96%87%EF%BC%89%E5%AD%97%E5%BD%A2)）
> ```bash
> sudo apt install fonts-noto
> sudo locale-gen zh_CN zh_CN.UTF-8
> sudo update-locale LC_ALL=zh_CN.UTF-8 LANG=zh_CN.UTF-8
> fc-cache -fv
> ```

默认备选字体列表如下：
```
"Arial", "Tahoma", "Helvetica Neue", "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Source Han Sans SC", "Noto Sans SC", "Noto Sans CJK JP", "WenQuanYi Micro Hei", "Apple Color Emoji", "Noto Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"
```

可在 `.env.*` 文件中添加 `default_fallback_fonts` 变量 来自定义备选字体

字体文件需要在系统目录下，或放置于自定义字体路径中

自定义字体路径默认为机器人运行目录下的 `data/fonts/` 文件夹，

可在 `.env.*` 文件中添加 `custom_font_path` 变量 自定义字体路径

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

# 以上结果为 PIL 的 Image 格式，若要直接 MessageSegment 发送，可以转为 BytesIO
output = BytesIO()
img.save(output, format="png")
await matcher.send(MessageSegment.image(output))
```

![2.png](https://s2.loli.net/2022/05/19/14EXViZQwcGUW5I.png)


- 使用 `BBCode`

```python
from nonebot_plugin_imageutils import text2image

# img: PIL.Image.Image
img = text2image("N[size=40][color=red]o[/color][/size]neBo[size=30][color=blue]T[/color][/size]\n[align=center]太强啦[/align]")

# 以上结果为 PIL 的 Image 格式，若要直接 MessageSegment 发送，可以转为 BytesIO
output = BytesIO()
img.save(output, format="png")
await matcher.send(MessageSegment.image(output))
```

![3.png](https://s2.loli.net/2022/05/19/VZAXsKB2x65q7rl.png)

目前支持的 `BBCode` 标签：
- `[align=left|right|center][/align]`: 文字对齐方式
- `[color=#66CCFF|red|black][/color]`: 字体颜色
- `[stroke=#66CCFF|red|black][/stroke]`: 描边颜色
- `[font=msyh.ttc][/font]`: 文字字体
- `[size=30][/size]`: 文字大小
- `[b][/b]`: 文字加粗


### 特别感谢

- [HibiKier/zhenxun_bot](https://github.com/HibiKier/zhenxun_bot) 基于 Nonebot2 和 go-cqhttp 开发，以 postgresql 作为数据库，非常可爱的绪山真寻bot
