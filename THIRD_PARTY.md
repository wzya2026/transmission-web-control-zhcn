# 来源、许可证和对应源码

本项目独立于各上游，保留上游版权、商标及许可证。根目录 MIT 只覆盖新增适配代码及构建工具，不改变随 SPK 或网页分发的第三方代码许可。

## Transmission Web Control

- 作者：栽培者 / ronggang。
- 仓库：https://github.com/ronggang/transmission-web-control
- 基线提交：`054e2edf7ee1ec859cec3ee5661a550481321a27`，版本 1.6.1。
- MIT 许可及原署名保留在 `licenses/Transmission-Web-Control-MIT.txt`、生成网页的 `LICENSE-transmission-web-control.txt` 中。
- 原源码中的第三方网页资源保留原文件及嵌入声明。本项目没有将其重新许可。所有公开修改可从 `src/`、`tools/build_twc.py` 和 `patches/` 审阅，固定上游可按 `sources.lock.json` 获取。

## Transmission 4.1.3

- 上游：https://github.com/transmission/transmission/tree/4.1.3
- 原作者允许按 GPLv2 或 GPLv3 分发，且有 OpenSSL 链接例外；声明保留在 `licenses/Transmission-COPYING.txt`，完整 GPL 文本在同目录。
- 本项目不修改核心程序和动态库。原始 SPK 内 16 个核心文件的校验值保留在 `release-manifest.json`。
- **对应上游源码**随 Release 提供 `transmission-4.1.3.tar.xz`，直接来自 [Transmission 4.1.3 官方源码发行包](https://github.com/transmission/transmission/releases/download/4.1.3/transmission-4.1.3.tar.xz)，含上游构建文件及 vendored 源码。下载无需 NAS 账号。

## SynoCommunity 套件构建工程

- 原包：https://synocommunity.com/package/transmission ，版本 4.1.3-31；确切下载 URL 和 SHA256 位于 `sources.lock.json`。
- 构建工程：https://github.com/SynoCommunity/spksrc
- 本项目固定与 4.1.3-31 对应的 Transmission Makefile 最新变更提交 `16b00abc5f7ff2ca75f716b6116c75f4a7dc0f25` 作为套件配方源码快照。原下载包没有提供全工程的构建提交证明，因此不声称该提交就是原包完整构建环境的取证结果。
- **套件配方、交叉构建脚本、补丁及依赖定义的源码归档**随 Release 提供 `spksrc-16b00abc5f7ff2ca75f716b6116c75f4a7dc0f25-source.tar.gz`。源码中 `spk/transmission`、`cross/transmission`、`cross/curl`、`cross/openssl3`、`cross/c-ares*`、`cross/zlib` 包含相应来源、版本、摘要及构建定义。
- SynoCommunity 构建工程许可证保留于 `licenses/SynoCommunity-LICENSE.txt`。Transmission 自身仍使用其原许可证。

## 随原包携带的库

原包包含 curl、OpenSSL、c-ares、zlib 及相关模块，均原样保留。这些组件具有各自的许可，源码中的版权声明和许可证不能因本项目 MIT 许可而被省略或替换。`licenses/` 保留 curl 8.4.0 的 COPYING、OpenSSL 3.5.7 的 Apache 2.0 文本、c-ares 1.34.2 的许可及 zlib 1.3.2 含许可的 README；源文件中的许可声明继续有效。

对应上游源码：

- curl 8.4.0：https://curl.se/download/curl-8.4.0.tar.xz
- OpenSSL 3.5.7：https://github.com/openssl/openssl/releases/tag/openssl-3.5.7
- c-ares 1.34.2：https://github.com/c-ares/c-ares/releases/tag/v1.34.2
- zlib 1.3.2：https://zlib.net/fossils/zlib-1.3.2.tar.gz

源码归档的 URL、大小及 SHA256 见 `corresponding-source.json`；发行附件的校验值见 Release 中的 `SHA256SUMS.txt`。下载程序源码可在与二进制相同的 Release 页面免费取得。后续重新分发时应同时保留来源、许可证和对应源码的可获取方式。
