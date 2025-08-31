# Image Cutter - 图像切割工具

[English](./README_en.md) | [中文](./README_cn.md)

A professional image cutting tool designed for splitting scanned thin section images with automatic optimal split calculation. Provides three usage methods: command-line version, GUI version, and standalone executable.

图像切割工具，专门用于分割扫描的薄片图像，支持自动计算最佳分割数量。提供命令行版本、GUI版本和独立可执行文件三种使用方式。

## Quick Start | 快速开始

### Standalone Executable (Recommended) | 独立可执行文件（推荐）

No Python installation required, just double-click to use:
无需安装Python环境，双击即可使用：

- Double-click `launch_gui.bat` (Launch ImageCutter GUI)
- Or directly run `dist/ImageCutter_GUI.exe`

### Python Source Version | Python源码版本

Requires Python 3.10 environment | 需要Python 3.10环境：

- GUI version | GUI版本: `python imageCutter_gui.py`
- Command-line version | 命令行版本: `python imageCutter.py`

## Features | 功能特性

- **Automatic Split Calculation | 自动计算分割数**: Based on image width (6500 pixels per segment) | 基于图像宽度自动计算最佳分割数（以6500像素为基准）
- **Multi-threading Processing | 多线程处理**: Uses thread pools to improve speed | 使用线程池提高处理速度
- **Quality Preservation | 质量保持**: Maintains original image quality | 保持原始图像质量，支持JPEG和PNG格式
- **Graphical Interface | 图形界面**: Intuitive GUI, no command-line knowledge required | 直观易用的GUI界面，无需命令行操作
- **Standalone Executable | 独立可执行**: 28MB executable without Python requirement | 无需Python环境的独立可执行文件（28MB）

## System Requirements | 安装要求

### Standalone Executable (Recommended) | 独立可执行版本（推荐）

- **System | 系统要求**: Windows 10 or higher | Windows 10 或更高版本
- **Memory | 内存要求**: 4GB or more recommended | 建议 4GB 或更多
- **No Additional Installation | 无需额外安装**: No Python environment required | 不需要Python环境或任何依赖包

### Python Source Version | Python源码版本

**Python Version | Python版本**: 3.10

```bash
pip install tqdm==4.66.1 pillow==10.1.0 numpy==1.26.0
```

## Usage Examples | 使用示例

### GUI Workflow | GUI操作流程

1. **Select Folder | 选择文件夹**: Click "Browse" button | 点击"浏览"按钮
2. **Set Parameters | 设置参数**: Configure split settings | 配置分割设置
3. **Start Processing | 开始处理**: Click "Start Processing" | 点击"开始处理"
4. **Monitor Progress | 监控进度**: Watch progress bar | 观察进度条
5. **View Results | 查看结果**: Check split files | 检查分割文件

### Command-line Example | 命令行示例

```bash
python imageCutter.py --folder_path "D:\images" --num_splits 3 --auto_split
```

## Documentation | 文档

For detailed documentation, please refer to:
详细文档请参考：

- **English Documentation | 英文文档**: [README_en.md](./README_en.md)
- **Chinese Documentation | 中文文档**: [README_cn.md](./README_cn.md)

## Version | 版本

**Current Version | 当前版本**: v1.2.0 (August 29, 2025)

## Contact | 联系方式

- **Author | 作者**: Kai Cao
- **Email | 邮箱**: caokai_cgs@163.com
- **Project | 项目**: [GMAS_Scripts/ImageCutter](https://github.com/Kai-FnLock/GMAS_Scripts)

---

**License | 许可证**: Full Copyright - All rights reserved | 保留所有权利

If this project helps you, please give it a star! | 如果这个项目对您有帮助，请给它一个星标！
