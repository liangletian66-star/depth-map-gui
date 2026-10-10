# 第三方组件与致谢

本项目本身只是界面外壳，核心能力来自以下开源项目与模型。它们都允许商用，
但保留了各自的署名要求，发布时请一并保留本文件与对应链接。

| 组件 | 用途 | 许可证 | 链接 |
|---|---|---|---|
| **reshot** | 视频 → 深度图 / 骨架 / 轮廓 | Apache-2.0 | https://github.com/maosika-ai/reshot |
| **Video-Depth-Anything-Small** | 深度估计模型权重（28.4M） | Apache-2.0 | https://github.com/DepthAnything/Video-Depth-Anything |
| PyTorch / torchvision | 推理框架 | BSD-3-Clause | https://pytorch.org |
| opencv-python-headless | 视频读写 | Apache-2.0 | https://github.com/opencv/opencv-python |
| huggingface_hub | 权重下载 | Apache-2.0 | https://github.com/huggingface/huggingface_hub |
| einops | 张量操作 | MIT | https://github.com/arogozhnikov/einops |
| easydict | 配置字典 | LGPL-3.0 | https://github.com/makinacorpus/easydict |
| tqdm | 进度条 | MIT / MPL-2.0 | https://github.com/tqdm/tqdm |
| tkinterdnd2 | 拖拽支持 | MIT | https://github.com/pmgagne/tkinterdnd2 |

## 重要说明

- **只使用 Small 模型**。Video-Depth-Anything 的 **Base / Large 模型是 CC-BY-NC-4.0（禁止商用）**，
  若替换为本项目的其他模型规格，请自行确认许可证。
- reshot 由 **Maosika（猫斯卡）AI 短剧生产系统**开源，引用请保留其仓库链接。
- 若引用 Video Depth Anything 论文：

  ```
  @article{video_depth_anything,
    title={Video Depth Anything: Consistent Depth Estimation for Super-Long Videos},
    author={Chen, Sili and Guo, Hengkai and Zhu, Shengnan and Zhang, Feihu and Huang, Zilong and Feng, Jiashi and Kang, Bingyi},
    journal={arXiv:2501.12375},
    year={2025}
  }
  ```

## 免责声明

请仅使用你有权处理的视频素材。将他人作品用于二次创作时，须遵守原作品版权与相关平台规则。
