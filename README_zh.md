# Antigravity NotebookLM 插件

[🌐 English Documentation](README.md)

这是一个企业级、完全事件驱动的 [Google NotebookLM](https://notebooklm.google.com/) 插件，专为 Antigravity 多智能体生态系统打造。本插件将复杂的 `notebooklm-py` 网页抓取与浏览器编排逻辑抽象成了一个严格管控、完全异步且确保 JSON 解析安全的智能体技能 (Agent Skill)。

## 🏗️ 系统架构

本插件的设计围绕着 Antigravity 的 **“零 SDK 侵入 (Zero-SDK)”** 与 **“事件驱动 (Event-Driven)”** 哲学，安全地缝合了本地 Agent 与 Google 云端私有 API。

```mermaid
graph TD
    A[Antigravity 智能体] -->|run_command| B(Python 桥接脚本)
    
    subgraph Local Sandbox [.venv 沙箱]
        B -->|re.search JSON 隔离提取| C{notebooklm-py 命令行}
        C -->|无头 Playwright 驱动| D[浏览器 Profile]
    end
    
    C <-->|HTTPS| E((Google NotebookLM 云端))
    
    A -.->|Native Wait (原生系统挂起)| B
    B -.->|Event Callback (唤醒信号)| A
    
    F[(Vector Lake 图谱)] -.->|双向同步| A
```

## 🌟 核心特性

### 1. 全系 9 大数字工件生成
插件已经动态映射并支持在对话界面中一键生成官方全部的 **9 大 NotebookLM 产物**：
- 🎙️ **Audio Overview (播客)** (支持自定义提示词注入)
- 📽️ **Video Overview (视频)** (支持自定义提示词注入)
- 🎬 **Cinematic Video (电影级视频)** (隐藏特性)
- 📊 **Slide Deck (幻灯片)**
- 🧠 **Mind Map (思维导图)**
- 📑 **Reports (研究报告)**
- 📇 **Flashcards (记忆卡片)**
- 📝 **Quiz (测验题)**
- 📈 **Infographic (信息图)** 与 **Data Table (数据表)**

### 2. 深度知识库管理
完全控制您特定的 Notebook 数据源：
- **AI 查询 (Ask)**：直接向特定的 Notebook 知识库发起追问，提取文献见解。
- **信源管理 (Source)**：支持列出当前所有源，添加新源，或通过底层 ID 物理删除冗余资料以防知识污染。
- **深度研究 (Deep Research)**：自动触发 Web/Drive 搜索并沉淀资料。

### 3. 被动事件驱动架构
NotebookLM 的音频或深层研报生成通常需要耗费数分钟。为了防止大模型陷入浪费 Token 的“死循环轮询”，本代理采用了底层的 `wait` 命令。任务下发后大模型将直接休眠，当云端生成完毕时，操作系统底层回调会瞬时唤醒 Agent。

### 4. I/O 毒素隔离 (JSON Bridge)
在桥接层采用了坚固的正则提取器 (Regex Extraction)。它能无视任何不可控的 Playwright 引擎升级警告或 Chromium 日志污染，精准过滤出最纯净的 JSON 返回给大模型，彻底消灭解析崩溃 (JSONDecodeError)。

### 5. 多媒体就地播放与图谱融合
下载的 `.wav` 与 `.mp4` 原始文件将不会变成一堆“垃圾代码文件”，Agent 会自动用 Markdown 组件对它们进行封装（通过绝对路径映射），使得音频播客可以直接在 Antigravity 的聊天 UI 中点击播放。同时，新建的 Notebook 也会自动登记进本地的双链逻辑湖 (Vector Lake) 中。

## 📂 目录结构

```text
config/plugins/notebooklm/
├── plugin.json                 # 插件元数据
├── README.md                   # 英文说明文档
├── README_zh.md                # 中文说明文档
├── agents/
│   └── notebooklm_researcher/  # 专职负责长时间 Deep Research 的挂机子代理
└── skills/
    └── notebooklm-core/
        ├── SKILL.md            # 执行契约与安全管控红线
        └── scripts/            # “物理隔离”的 Python 桥接执行层
            ├── .venv/          # 独立的 Playwright 运行环境
            ├── auth_bridge.py      
            ├── notebook_bridge.py  
            └── generate_bridge.py   
```

## 🚀 部署与鉴权

因为 NotebookLM 依赖于 Google 的内网 API，必须依赖真实浏览器的 Cookie。**已建立安全门控，Agent 被严禁在未获用户同意前擅自盗取 Cookie。**

在一台全新主机上初始化该插件：

1. **进入隔离沙箱：**
   ```powershell
   cd ~/.gemini/config/plugins/notebooklm/skills/notebooklm-core/scripts
   .\.venv\Scripts\Activate.ps1
   ```
2. **拉起交互式登录：**
   ```powershell
   notebooklm login
   ```
   *这将拉起一个真实的 Chromium 浏览器，登录您的 Google 账号后即可关掉。*

3. **测试 Agent 桥接连通性：**
   ```bash
   python auth_bridge.py check
   ```

## 🤖 交互范例

只需对 Antigravity 下达口语化指令：
> *"帮我新建一个叫‘量子计算’的 NotebookLM 项目，把这个维基百科链接喂进去。然后生成一份双人对话播客让我听一下。"*

Agent 会全自动执行：
1. 拦截检查 Cookie 鉴权。
2. 创建 Notebook 并注入链接。
3. 触发 Podcast 生成，并在底层拉起原生 `wait` 然后休眠。
4. 几分钟后被自动唤醒，下载音频。
5. 吐出一个内嵌音频播放器的精美 Markdown 总结卡片给您！
