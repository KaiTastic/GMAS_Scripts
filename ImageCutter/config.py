# Image Cutter 项目配置

## 项目信息
PROJECT_NAME = "Image Cutter"
PROJECT_VERSION = "1.2.0"
AUTHOR = "Kai Cao"
EMAIL = "caokai_cgs@163.com"

## Python环境要求
PYTHON_VERSION = "3.10+"
REQUIRED_PACKAGES = [
    "tqdm==4.66.1",
    "Pillow==10.1.0", 
    "numpy==1.26.0"
]

## 构建配置
BUILD_TOOL = "PyInstaller 6.11.1"
EXECUTABLE_NAME = "ImageCutter_GUI.exe"
BUILD_DIR = "dist/"

## 默认设置
DEFAULT_SPLIT_WIDTH = 6500  # 像素
DEFAULT_OUTPUT_QUALITY = 95  # JPEG质量
DEFAULT_EXCLUDE_STRING = "_split_"
SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]

## 文件路径
MAIN_GUI_FILE = "imageCutter_gui.py"
MAIN_CLI_FILE = "imageCutter.py"
SPEC_FILE = "imageCutter_gui_simple.spec"
BUILD_SCRIPT = "构建图像切割器_GUI.bat"
LAUNCH_SCRIPT = "启动图像切割器_GUI.bat"
