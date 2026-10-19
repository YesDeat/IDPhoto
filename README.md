# IDPhoto

电子证件照处理工具：上传一张照片，换底色（蓝 / 白 / 红 / 灰 / 黑）、裁切到**一寸 / 两寸**标准尺寸、可调**分辨率(DPI)** 与**输出文件大小(KB)**，一键生成证件照。Python + Pillow，带图形界面和命令行两种模式。

ID photo tool: pick a photo, change background (blue/white/red/gray/black), crop to **1-inch / 2-inch** standard size, adjust **DPI resolution** and **output file size (KB)**, one-click export. Python + Pillow, GUI and CLI.

## 功能 / Features

- **换底色**：采样四边背景色 + 容差替换（带羽化），适合纯色背景的证件照。/ Background swap by sampling border color + tolerance (feathered).
- **尺寸**：一寸 (25×35mm)、两寸 (35×49mm)，自动居中裁切到对应宽高比。/ 1-inch, 2-inch, center-cropped.
- **分辨率**：DPI 可调（默认 300），输出像素随之变化。/ Adjustable DPI (default 300).
- **文件大小**：目标 KB 可选，自动调节 JPEG 质量逼近。/ Target KB: auto-adjust JPEG quality.
- **可编辑**：底色、尺寸、DPI、KB、容差全部可在界面调整。/ All editable in the UI.

## 用法 / Usage

图形界面 / GUI：

```powershell
py idphoto.py
```

命令行 / CLI：

```powershell
py idphoto.py input.jpg --color 蓝 --size 一寸 --dpi 300 --kb 50
```

参数 / Args: `--color 蓝|白|红|灰|黑|无`, `--size 一寸|两寸`, `--dpi 300`, `--kb 50`(0=不限), `--thr 70`(背景容差), `--out 输出路径`.

## 依赖 / Dependencies

仅 Pillow / Pillow only:

```powershell
pip install pillow
```

## 说明 / Notes

- 背景替换基于**颜色距离**，对纯色/近纯色背景效果最好；复杂背景（花纹、与人物同色）可能残留或误删，可调大「背景容差」或手动抠图后再处理。/ Color-based bg swap works best on plain backgrounds.
- 输出为 JPEG（便于控制 KB）；如需透明 PNG，可自行改 `process()` 的保存格式。/ Output is JPEG for size control.
- 运行：`py idphoto.py`，控制台黑窗已自动隐藏 / console hidden.

## 文件 / Files

- `idphoto.py` 主程序 / main
- `requirements.txt` 依赖 / deps
- `README.md` 说明 / docs
- `.gitignore`
