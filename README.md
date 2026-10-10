# 视频深度图工具（GUI）

把一段原视频丢进去，自动输出**黑白深度视频**（近处偏白、远处偏黑）。
用于 AI 漫剧 / AI 短剧的动作迁移：深度视频只保留**走位、动作、运镜、场景结构**，
丢掉人脸、衣服、光照、画风，作为下游视频生成模型的参考视频（如 Seedance、MiniMax H3、Wan VACE）。

> **本项目只是一个图形界面外壳。** 真正的深度估计由 [reshot](https://github.com/maosika-ai/reshot)（Apache-2.0）完成。

A drag-and-drop GUI wrapper that turns a video into a grayscale **depth video** for AI anime/short-drama motion transfer. Powered by [reshot](https://github.com/maosika-ai/reshot).

---

## 功能

- 把视频**拖进窗口**即自动处理，无需命令行
- 批量拖入多个视频，依次处理
- 输出规格可选：Seedance 2.0/2.5、MiniMax H3、Wan VACE
- 全程本地运行，**视频不外传**
- 关闭窗口即结束所有后台进程，无残留

## 环境要求

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows / macOS / Linux |
| Python | 3.10 – 3.12（reshot 依赖） |
| ffmpeg | 需在 PATH 中 |
| 显卡 | 可选。NVIDIA 独显会快很多；无独显走 CPU（慢） |

## 安装

```bash
git clone https://github.com/liangletian66-star/depth-map-gui.git
cd depth-map-gui

# 1. 建虚拟环境
python -m venv venv

# 2. 装 PyTorch（按你的显卡选一个）
#    NVIDIA 50 系（Blackwell / sm_120）—— 必须用 cu128
venv/Scripts/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
#    NVIDIA 40 系及更早 —— cu124 即可
# venv/Scripts/pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
#    纯 CPU
# venv/Scripts/pip install torch torchvision

# 3. 装其余依赖（macOS/Linux 把 venv/Scripts 换成 venv/bin）
venv/Scripts/pip install -r requirements.txt
```

> **国内网络提示**：脚本默认把 HuggingFace 镜像设为 `hf-mirror.com`，
> 首次运行会自动下载约 **111 MB** 的模型权重（Video-Depth-Anything-Small），
> 缓存在项目目录下的 `models/`。

## 使用

```bash
# 直接运行
python src/depth_gui.py
```

窗口打开后，把视频拖进虚线框即可。成品在 `output/` 目录。

## 打包成 exe（可选，Windows）

```bat
scripts\build_exe.bat
```

依赖同目录的 `venv`，打包产物只是界面外壳（约 11 MB），**不包含** PyTorch，
所以发布 exe 时需要让用户先把 `venv` 装好。

## 目录结构

```
depth-map-gui/
├── src/depth_gui.py      # 主程序
├── assets/icon.ico       # 图标
├── scripts/build_exe.bat # 打包脚本
├── requirements.txt
└── README.md
```

## 已知问题

- **RTX 50 系（Blackwell）必须用 PyTorch cu128**。cu124 会「显示 CUDA 可用」但实际跑不了，
  因为硬件架构是 `sm_120`，旧版编译时还没有这代指令集。
- **HF 下载偶发中断**：Windows 下 HuggingFace 的缓存软链接可能不生成，导致权重文件为 0 字节、
  报 `EOFError`。删掉 `models/` 重新下载，或手动把 `models/hub/.../blobs/` 里的真实权重
  复制到 `snapshots/.../` 对应文件名下即可。
- 视频建议 **15 秒以内**（下游模型限制），分辨率不要低于 640×360。

## 许可证

本项目代码以 **MIT** 许可证发布，见 [LICENSE](LICENSE)。
第三方组件与模型的许可证见 [NOTICE.md](NOTICE.md)。
