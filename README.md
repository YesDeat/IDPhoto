# IDPhoto

电子证件照处理工具：上传一张照片，换底色（蓝 / 白 / 红 / 灰 / 黑）、裁切到**一寸 / 两寸**标准尺寸、可调**分辨率(DPI)** 与**输出文件大小(KB)**，一键生成证件照。Python + Pillow + rembg，带图形界面和命令行两种模式。

ID photo tool: pick a photo, change background (blue/white/red/gray/black), crop to **1-inch / 2-inch** standard size, adjust **DPI resolution** and **output file size (KB)**, one-click export. Python + Pillow + rembg, GUI and CLI.

## 功能 / Features

- **换底色**：两种模式任选 / two background modes:
  - **AI 智能抠图（rembg）**：勾选「AI 智能抠图」，用 U²-Net/bria 模型自动分离人物与背景，再合成到目标底色，适合**复杂背景**照片。/ AI matting via rembg, robust on complex backgrounds.
  - **颜色替换**：不勾选时，采样四边背景色 + 容差替换（带羽化），适合纯色背景。/ Color-distance swap, good for plain backgrounds.
- **尺寸**：一寸 (25×35mm)、两寸 (35×49mm)，自动居中裁切到对应宽高比。/ 1-inch, 2-inch, center-cropped.
- **分辨率**：DPI 可调（默认 300），输出像素随之变化。/ Adjustable DPI (default 300).
- **文件大小**：目标 KB 可选，自动调节 JPEG 质量逼近。/ Target KB: auto-adjust JPEG quality.
- **可编辑**：底色、尺寸、DPI、KB、容差、AI 开关全部可在界面调整。/ All editable in the UI.
- **不卡界面**：AI 推理在后台线程运行，处理时界面保持响应并显示进度，不再「未响应」。/ Processing runs in a background thread so the UI never freezes.

## 用法 / Usage

图形界面 / GUI：

```powershell
py idphoto.py
```

命令行 / CLI：

```powershell
py idphoto.py input.jpg --color 蓝 --size 一寸 --dpi 300 --kb 50 --ai
```

参数 / Args: `--color 蓝|白|红|灰|黑|无`, `--size 一寸|两寸`, `--dpi 300`, `--kb 50`(0=不限), `--thr 70`(背景容差), `--ai`(启用 AI 抠图), `--out 输出路径`.

## 依赖 / Dependencies

```powershell
pip install pillow rembg[cpu]
```

- **AI 模型**：首次使用 AI 抠图时，rembg 会自动下载模型（约 **1GB**，首次几十秒~1分钟，之后缓存复用）。/ rembg auto-downloads its ~1GB model on first use.
- 模型默认下载到 `~/.u2net`；本机若设置了 `U2NET_HOME` 环境变量则下载到该目录（例如 `D:\codeby\u2net`，避免占 C 盘）。/ Model dir respects `U2NET_HOME`.
- 仅 CPU 推理时选 `rembg[cpu]` 即可；有 NVIDIA 显卡可换 `rembg[gpu]`。/ Use `rembg[gpu]` if you have a CUDA GPU.

## 说明 / Notes

- **AI 模式首次较慢**：bria 模型约 1GB，CPU 推理 20-60 秒；界面会显示「处理中…」，期间可随意拖动窗口。/ First AI run is slow; UI stays responsive.
- **颜色替换模式**基于颜色距离，对纯色/近纯色背景效果最好；复杂背景建议直接用「AI 智能抠图」。/ Prefer AI mode for complex backgrounds.
- 输出默认 JPEG（便于控制 KB）；AI 模式选底色「无」时会输出透明 PNG。/ AI + color "无" → transparent PNG.
- 控制台黑窗已自动隐藏 / console hidden.

## 文件 / Files

- `idphoto.py` 主程序 / main
- `requirements.txt` 依赖 / deps
- `README.md` 说明 / docs
- `.gitignore`
