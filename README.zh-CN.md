<div align="center">
  <p>
    <a align="center" href="https://github.com/KIvoy/nikke-assistant" target="_blank">
      <img width="20%" src="https://github.com/KIvoy/nikke-assistant/blob/main/images/nikke_icon.jpg"></a>
  </p>

[English](README.md) | [简体中文](README.zh-CN.md)
<br>
</div>

# 指挥官助理

一个 python 桌面应用程序，可以帮助 胜利女神：妮姬 中的指挥官完成日常

## 免责声明

指挥官助理不参与任何游戏文件、内存或网络流量干扰。它仅使用图像处理和输入模拟来完成不涉及与其他玩家竞争或获得对其他玩家的不公平优势的任务。可以用助手完成的所有事情都可以用玩家手动完成。

虽然根据 SU 的历史，您不太可能因使用助手而被禁止，但对于游戏公司因您的使用而可能采取的任何潜在行动，助手概不负责。

<b>请您自己承担风险使用</b>.

## 在windows上运行打包好的exe

-   下载压缩的发布包
-   解压到你想要的位置
-   打开 Nikke: Goddess of Victory 游戏应用程序
-   运行nikke-assistant.exe

## 常见问题

-   <b>助手说“找不到游戏窗口”，根本不启动任何任务，或在任务处随机停止</b>

确保使用重新加载游戏功能并检查您的游戏窗口大小是否已调整为 591x1061。大多数情况下助理应该在那时工作。

如果仍未找到游戏窗口或窗口未调整大小，则可能是由于您的客户端版本，助手无法识别游戏窗口的名称。使用选择游戏窗口功能循环浏览应用程序列表并找到您的实际游戏窗口，然后再次单击重新加载游戏。

-   <b>我如何使用重复活动关卡功能？</b>

虽然助手会在每个新活动中更新，但它只是根据我对重复级别的偏好进行更新，可能不适合您的需要。

将文件调整到您自己的水平以提前重复非常容易。只需截取您从“活动”页面一直点击到您想要重复的关卡的所有图像。将所有这些屏幕截图存储在`images/nikke/home/event/<你的活动名字>/`并将它们命名为`step_1.png`,`step_2.png`等。如果需要，您可以在同一目录中查看以前活动的屏幕截图示例。最后，不要忘记在设置中更改要重复的活动<你的活动名字>你刚刚创建的。现在，当您单击重复活动关卡时，它应该会准确地重复您需要的内容。

-   <b>我的电脑很慢，有时加载需要很长时间，助手没有等待足够长的时间</b>

您可以通过更改`pre_action_delay`和`post_action_delay`在`NIKKE_ASSISTANT.INI`.该值越大，动作之间的延迟越多（以秒为单位）。

您还可以设置`log_to_file=False`为可能更快的助手禁用日志记录。但是，如果发生任何事情，您将无法查看错误日志。

-   <b>我的问题不在上述范围内，我不知道发生了什么</b>

首先，请记住官方只支持简体中文版游戏。如果您使用任何其他语言环境，则无法保证所有功能都能正常工作！如果你真的想将它用于你自己的语言环境，你可以随时提交一个 PR，其中包含你自己语言环境中的资源（例如图像和建议答案）。

如果您有任何其他问题，请随时访问[讨论](https://github.com/KIvoy/nikke-assistant/discussions "Nikke Assistant Discussion")如果提出错误，请提交包含详细说明、屏幕截图、app_log 和 app_error 文件。

## 在 Windows 上运行源代码

-   有安装要求`requirements.txt`
-   安装了python
-   已安装 tesseract 并指向正确的目录
-   跑步`py nikke_interface.py`
-   生成您可能想要运行的语言环境文件`py setup.py compile_catalog --domain nikke-assistant --directory ./locale --locale zh`, 将语言环境替换为相应的语言环境。
-   Windows应用程序应该启动
-   （可选）您可能需要授予它管理员权限才能使某些功能正常工作

## 在 Windows 上打包为 .exe

-   如果还没有创建虚拟环境`py -m venv venv`
-   启动虚拟环境`& ./venv/Scripts/Activate.ps1`
-   安装要求`pip install -r requirements.txt`
-   运行打包命令`bash package.sh`，确保更改目录
    -   或者使用 auto-py-to-exe 打包一切
-   从任一处收集打包的文件夹`dist`或者`output`目录取决于您使用的方法或您的自定义目录

## 语言支持

-   您可以更改游戏语言和用户界面语言`NIKKE_ASSISTANT.INI`
    -   迄今为止`en`对于英语和`zh`UI 方面的简体中文
    -   仅正式支持简体中文客户端语言环境。尚未实现对英文客户端的支持，您可能会遇到一些错误
    -   随意用您的语言创建资源以支持相应的客户端（例如图像或咨询答案）。

## Releases

-   您可以在相应的发布标签中下载最新版本

## 合作

-   热烈欢迎！欢迎任何贡献，包括但不限于：
    -   本地化（用户界面或游戏客户端语言）
    -   改进现有功能
    -   合理的重构（上帝保佑！）
    -   任何能让体验更好的东西

## 特别感谢

- 感谢 https://nikke.gamekee.com/575965.html 提供的最新妮姬咨询情报。