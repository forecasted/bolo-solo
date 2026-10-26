<p align = "center">
<img alt="Bolo" src="/pic/bolo-circle.png" height="200px" width="200px">
<br><br>
基于 Java 的菠萝博客系统，简单易部署，精致主题，贴心服务，专为程序员设计。
<br><br>
<img src="http://img.shields.io/badge/license-AGPLv3-orange.svg?style=flat-square">
<img src="https://img.shields.io/github/last-commit/adlered/bolo-solo.svg?style=flat-square">
<img src="https://img.shields.io/github/issues-pr-closed/adlered/bolo-solo.svg?style=flat-square">
<img src="https://img.shields.io/github/downloads/adlered/bolo-solo/total?style=flat-square">
<img src="https://img.shields.io/github/v/release/adlered/bolo-solo?style=flat-square">
<img src="https://img.shields.io/github/commit-activity/y/adlered/bolo-solo?style=flat-square">
<br>
<img src="https://img.shields.io/github/languages/code-size/adlered/bolo-solo.svg?style=flat-square">
<img src="https://img.shields.io/github/repo-size/adlered/bolo-solo?style=flat-square">
<img src="https://img.shields.io/github/languages/count/adlered/bolo-solo?style=flat-square">
<img src="https://img.shields.io/github/languages/top/adlered/bolo-solo?style=flat-square">
<img src="https://img.shields.io/github/issues/adlered/bolo-solo?style=flat-square">
<img src="https://img.shields.io/github/issues-closed-raw/adlered/bolo-solo?style=flat-square">
<br>
<img src="https://img.shields.io/github/forks/adlered/bolo-solo?style=flat-square">
<img src="https://img.shields.io/github/stars/adlered/bolo-solo?style=flat-square">
<img src="https://img.shields.io/github/watchers/adlered/bolo-solo?style=flat-square">
<br>
<a href="https://www.jetbrains.com/?from=bolo-solo"><img src="/pic/jetbrains.png" width="146px" height="158px"></a>
</p>

****

## ❤ 令人放心的全面免费服务

### ✅ 贴心的技术支持

* 有问必答的用户交流群，轻松气氛，社恐无惧
* 舒心提问，耐心讲解，博客维护团队为你解答
* 免费远程服务，解决疑难杂症
* 菠萝博客及全部增值服务永久免费，永久更新

### 🌱 我是小白，装不好怎么办？

不用担心安装问题，我们提供完善的文档，提供所有部署方式的安装、升级方式，通过简单的几步就可启动。  
如果你在跟随教程安装的过程中出现任何问题，菠萝博客用户群会有作者以及维护者随时待命，**免费解答、远程帮助**，QQ 用户群请点击最下方的链接。

## 🌸 欣赏

[上手尝试所有皮肤，点我](https://doc.stackoverflow.wiki/web/#/7?page_id=88)

<p align="center">✨ 全新主题，支持黑暗模式</p>

<img src="/preview/1.png"/>
<img src="/preview/2.png"/>
<img src="/preview/3.png"/>

<p align="center">📈 后台管理，酷炫统计表，完整黑暗模式支持</p>

<img src="/preview/4.png"/>

<p align="center">🔍 搜索界面，一搜即达</p>

<img src="/preview/5.png"/>

<p align="center">📸 登录界面，定期自动更新主题美图</p>

<img src="/preview/6.png"/>

## 为什么选择 Bolo

1. 完整的教程文档，完善的交流答疑
2. 精美皮肤常更新
3. 支持将文章自动备份至 GitHub 仓库 [示例](https://github.com/adlered/bolo-blog)
4. 超酷的数据统计表
5. 本地登录、评论，支持备案模式（隐藏登录、评论及搜索入口）
6. 支持 Tomcat、Docker 快速部署
7. 邮件提醒功能，不怕错过博客中的新评论，回复他人评论也会发邮件提醒他人
8. 强大的 Vditor 编辑器，支持 `所见即所得`、`即时渲染`、`分屏预览` 三种模式，额外支持通过 [Lute_HTTP](https://github.com/88250/lute-http) 渲染
9. 支持自定义图床（阿里云、又拍云、七牛云、腾讯云）
10. 轻型防火墙功能，阻止恶意访问，保证博客正常运行
10. 强大的 Markdown 编辑器（使用 Vditor）支持大纲、数学公式、脑图、图表、流程图、甘特图、时序图、五线谱、多媒体、语音阅读、标题锚点、代码高亮及复制、graphviz 渲染
11. 支持黑暗模式，随系统设置自动切换，保护视力
12. 看板娘+，在线更新海量看板娘资源
13. 如果你是 [Solo](https://github.com/88250/solo) 用户，还可将 Solo 的数据一键迁移到 Bolo；如果你对 Bolo 不满意，还可以一键迁回至 Solo
14. Server 酱推送功能，在微信上接收你的博客动态
15. 自动生成“我在 GitHub 上的开源项目”文章功能，让博客的访客更好地了解你的 GitHub 履历

## 博客安装使用教程文档

### [👉 QQ用户群 | 安装教程 | 从Solo迁移 | Bolo介绍 | 常见问题 👈](https://doc.stackoverflow.wiki/web/#/7?page_id=46)

## Java 21 构建与运行

构建需要 JDK 21 或更新版本，运行需要 Java 21 或更新版本。Maven 使用 `--release 21` 限制字节码和 Java API 版本，因此也可以使用 JDK 25 为 Java 21 编译。

```bash
mvn -Pci -Dlicense.skip=true package
```

产物为 `target/bolo.war`，解压后的独立运行目录为 `target/bolo/`。配置 `WEB-INF/classes/local.properties` 中的数据库连接后，可在该目录启动：

```bash
java -cp "WEB-INF/lib/*:WEB-INF/classes" org.b3log.solo.Starter
```

`-Dlicense.skip=true` 用于避免构建过程自动改写源文件的许可证头；测试阶段正常执行。Docker 构建、运行镜像和发布工作流也使用 Java 21。

本机 Maven 中国镜像配置保存在 `~/.m2/settings.xml`，按阿里云、华为云、Maven Central 的顺序解析依赖和插件；该文件属于当前用户的全局设置，不会打包到 WAR 中。

## 静态资源与外部域名

固定的前端资源随项目一起发布，无须在运行时访问 CDN。`src/main/webapp/vendor/` 保存第三方样式、脚本、字体和编辑器依赖；看板娘贴图保存在 `src/main/webapp/plugins/kanbanniang/assets/model/`。Maven 打包 WAR 时会包含这些文件，部署时应完整更新 webapp，并刷新浏览器缓存。

| 原外部来源 | 本地处理 |
| --- | --- |
| `ftp.stackoverflow.wiki` | 登录、搜索、后台、主题和看板娘资源均改为本地路径；公告改为项目公告链接，版本检查使用 GitHub Releases API |
| `unpkg.com`、`cdn.jsdelivr.net` | 看板娘贴图、字体、画廊组件、前端库及其间接依赖全部打包 |
| `file.fishpi.cn` | Vditor 3.8.13、表情、代码高亮、公式和流程图依赖改为本地资源 |
| `fonts.googleapis.com`、字体文件 CDN | Montserrat、Titillium Web、Fira Sans 字体随项目发布 |
| `at.alicdn.com`、`use.fontawesome.com` | 图标字体与加载脚本改为本地文件 |
| `view.moezx.cc`、`static.2heng.xin`、`img.lonuslan.com`、`pic.stackoverflow.wiki` | 固定主题图片、光标、默认头像和图标改为本地资源 |
| `lab.lepture.com`、`player.vimeo.com` | GitHub 卡片页面和 Vimeo 播放器脚本改为本地文件 |
| `programmingwithlove.stackoverflow.wiki`、背景图 API | 登录页及樱花主题使用随项目发布的背景图 |
| `sdk.jinrishici.com`、`zz.bdstatic.com` | SDK 脚本改为本地文件，业务 API 请求仍保留 |
| `google-analytics.com`、`static.duoshuo.com` | 移除上游演示统计代码；停用已失效的多说脚本，使用博客自带评论 |
| `registry.npm.taobao.org`、旧 npm 镜像 | 构建锁文件改为 npm 官方源，保留依赖版本和完整性校验 |

旧 Butterfly 随机背景、评论装饰图和证书失效的页头图片使用已有的本地背景替代；失效的网格、光标、默认图标以及 Sakura 暗色背景、装饰 GIF 也提供了本地替代。Sakura 的旧 Live2D 随机贴图服务改用本地模型与默认服装。

静态资源本地化后，下列功能仍会按需联网：

| 域名或来源 | 用途 |
| --- | --- |
| `api.github.com`、`github.com` | 版本检查、授权、仓库数据和同步 |
| `ld246.com`、`fishpi.cn` | 社区登录、文章或评论同步等集成功能 |
| `v2.jinrishici.com`、`api.imjad.cn` | 今日诗词和看板娘语录接口 |
| 百度站点推送接口 | 主题的搜索引擎收录推送 |
| Gravatar、QQ、GitHub 头像域名 | 用户自己的头像数据 |
| YouTube、Vimeo、网易云等媒体来源 | 文章作者嵌入的音视频及缩略图 |
| 配置的 Lute、图床、邮件和通知服务 | 已有的服务端可选集成 |
| GitHub 导出模板中的徽章和统计图接口 | GitHub README 的动态数据 |

`report.stackoverflow.wiki:4399` 的用户体验改进计划已停用：新安装默认关闭，旧数据库中的开启设置也不会触发访问统计或错误日志上报，后台不再提示加入计划。

已保存的旧默认站点图标和默认头像会在展示时使用本地文件；文章正文、自定义用户头像、友情链接和后台自定义 HTML 中由用户保存的外链不会自动改写。需要完全离线运行时，还应检查这些内容和启用的在线集成。

本地资源增加了部署包体积，主要来自看板娘贴图。基础模型已随应用发布；如需额外模型压缩包，可显式设置 JVM 参数 `-Dbolo.kanbanniang.modelArchiveUrl=https://你的地址/models.zip`，默认启动不会下载扩展包。

第三方文件的来源、版本和 SHA-256 校验值记录在 `src/main/webapp/vendor/sources.json`；本地调整另见 `src/main/webapp/vendor/NOTICE.txt`。可运行 `python3 scripts/check-static-resources.py` 检查模板路径、CSS 字体和图片、模型文件及校验值。
