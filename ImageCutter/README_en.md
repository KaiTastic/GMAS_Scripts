# Image Cutter - Image Splitting Tool

A professional image cutting tool designed for splitting scanned thin section images with automatic optimal split calculation. Provides three usage methods: command-line version, GUI version, and standalone executable.

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Project Structure](#project-structure)
- [Interface Preview](#interface-preview)
- [System Requirements](#system-requirements)
- [Usage](#usage)
- [Parameters](#parameters)
- [How It Works](#how-it-works)
- [Output Files](#output-files)
- [Usage Examples](#usage-examples)
- [Important Notes](#important-notes)
- [Troubleshooting](#troubleshooting)
- [Version History](#version-history)
- [Related Documentation](#related-documentation)
- [Contributing](#contributing)
- [Contact](#contact)

## Quick Start

### Method 1: Standalone Executable (Recommended)

No Python installation required, just double-click to use:

- Double-click `launch_gui.bat` (Launch ImageCutter GUI)
- Or directly run `dist/ImageCutter_GUI.exe`

### Method 2: Python Source Version

Requires Python 3.10 environment:

- GUI version: `python imageCutter_gui.py`
- Command-line version: `python imageCutter.py`

## Features

- **Automatic Split Calculation**: Automatically calculates optimal split count based on image width (6500 pixels per segment)
- **Multi-threading Processing**: Uses thread pools to improve processing speed
- **Quality Preservation**: Maintains original image quality, supports JPEG and PNG formats
- **Smart Detection**: Automatically detects inconsistent split parameters and logs them
- **Overwrite Protection**: Automatically skips existing split files
- **Graphical Interface**: Intuitive and user-friendly GUI, no command-line knowledge required
- **Real-time Monitoring**: Progress bars and status display for real-time processing updates
- **Detailed Logging**: Complete operation logs for tracking and debugging
- **Standalone Executable**: Independent executable file (28MB) without Python environment requirement
- **One-click Launch**: Quick startup through batch scripts
- **Auto Build**: Provides auto-build scripts to regenerate executable files

## Project Structure

```
ImageCutter/
├── dist/
│   └── ImageCutter_GUI.exe          # Standalone executable (28MB)
├── build/                           # Build temporary folder (auto-generated)
├── __pycache__/                     # Python cache folder (auto-generated)
├── testImageData/                   # Test image data
│   ├── 4423-1-01-05-XPL.jpg
│   ├── 4423-1-11-15-PPL.jpg
│   ├── 4423-2-091-095-XPL.jpg
│   ├── 4423-2-096-098-PPL.jpg
│   ├── 4423-2-096-098-XPL.jpg
│   └── 4423-2-99-100-XPL.jpg
├── launch_gui.bat                   # Quick launch script (recommended)
├── build_gui.bat                    # Rebuild executable script
├── setup_environment.bat           # Auto-install Python environment and dependencies
├── test_project.bat                 # Project integrity test script
├── clean_project.bat               # Clean temporary files and cache script
├── project_info.bat                # View project details
├── imageCutter_gui.py              # GUI version source code (main program)
├── imageCutter.py                  # Core functionality module
├── imageCutter_gui_simple.spec     # PyInstaller configuration file
├── requirements.txt                # Python dependencies list
├── config.py                       # Project configuration file
├── .gitignore                      # Git version control ignore file
└── README.md                       # Project documentation
```

### Main File Descriptions

**Core Program Files:**

- `ImageCutter_GUI.exe`: Standalone executable, runs without Python environment
- `imageCutter_gui.py`: GUI version source code with graphical interface and multi-threading
- `imageCutter.py`: Core functionality module containing image processing algorithms

**Convenience Batch Scripts:**

- `launch_gui.bat`: Smart launch script (prioritizes .exe, fallback to Python version)
- `build_gui.bat`: Auto-build standalone executable
- `setup_environment.bat`: One-click Python dependency environment installation
- `test_project.bat`: Comprehensive project integrity and functionality testing
- `clean_project.bat`: Clean temporary files, cache, and test data
- `project_info.bat`: View project status, version, and environment information

**Configuration Files:**

- `requirements.txt`: Precise Python dependency version list
- `config.py`: Project configuration and constant definitions
- `.gitignore`: Git version control ignore rules
- `imageCutter_gui_simple.spec`: PyInstaller packaging configuration

## Interface Preview

### GUI Version Features:

- **User-friendly Interface**: All parameters set through graphical controls, no command memorization needed
- **Folder Browser**: Click button to select target folder
- **Real-time Progress Display**: Progress bar shows current processing progress and completion percentage
- **Detailed Processing Log**: Scrollable text area displays detailed processing information
- **One-click Stop Function**: Can stop ongoing processing tasks at any time
- **Smart Parameter Validation**: Automatically checks input parameter validity
- **Multi-format Support**: Dropdown menu for selecting supported image formats

## System Requirements

### Standalone Executable Version (Recommended)

- **System Requirements**: Windows 10 or higher
- **Memory Requirements**: 4GB or more recommended
- **Disk Space**: At least 100MB available space
- **No Additional Installation**: No Python environment or dependencies required

### Python Source Version

**Python Version**: 3.10
**Dependencies**:

```bash
pip install tqdm==4.66.1 pillow==10.1.0 numpy==1.26.0
# tkinter is a built-in Python module, no additional installation required
```

## Usage

### Method 1: Standalone Executable (Simplest)

**Quick Launch (Recommended):**

1. Double-click `launch_gui.bat`
2. The program will automatically check files and launch the GUI interface

**Direct Run:**

- Double-click `dist/ImageCutter_GUI.exe`

**Features:**

- No Python environment installation required
- One-click launch, ready to use
- Complete graphical interface functionality
- Automatic error detection and prompts

### Method 2: Python GUI Version

**Run Method:**

```bash
python imageCutter_gui.py
```

**Or use batch file:**

```bash
# Double-click to run
launch_gui.bat
```

### Method 3: Command-line Version

**Basic Usage:**

```bash
python imageCutter.py --folder_path "D:\path\to\images" --num_splits 5 --auto_split
```

### GUI Operation Workflow (Applies to all GUI versions)

1. **Select Folder**: Click "Browse" button to select folder containing images
2. **Set Parameters**:
   - Split count: Use spinner to set (recommended to keep auto-calculation)
   - Auto split: Check to automatically use calculated optimal split count
   - File format: Dropdown select (.jpg, .png, .bmp, etc.)
   - Exclude string: Set filename patterns to skip
3. **Start Processing**: Click "Start Processing" button
4. **Monitor Progress**: Watch progress bar and real-time log output
5. **View Results**: Check split image files after processing completion

### Rebuild Executable

To rebuild the executable file:

```bash
# Double-click to run
build_gui.bat
```

Or manually build:

```bash
pyinstaller imageCutter_gui_simple.spec
```

## Parameters

| Parameter         | Type   | Required | Default   | Description                    |
| ----------------- | ------ | -------- | --------- | ------------------------------ |
| `--folder_path` | string | Yes      | -         | Image folder path              |
| `--num_splits`  | int    | Yes      | -         | Number of split segments       |
| `--auto_split`  | flag   | No       | False     | Auto-use calculated split count|
| `--suffix`      | string | No       | ".jpg"    | File suffix to search for      |
| `--string`      | string | No       | "_split_" | Filename string to exclude     |

## How It Works

1. **File Scanning**: Recursively searches for image files in specified folder
2. **Filter Processing**: Excludes already split files (containing `_split_` string)
3. **Split Calculation**: Calculates optimal split count based on image width (6500 pixels/segment)
4. **Consistency Check**: Compares set split count with calculated split count
5. **Image Splitting**: Splits images according to calculated width
6. **Parallel Saving**: Uses thread pool to save split images in parallel

## Output Files

### Split Images

- **Naming Format**: `original_filename_split_number.extension`
- **Example**: `sample.jpg` → `sample_split_1.jpg`, `sample_split_2.jpg`, ...

### Log Files

- **Filename**: `inconsistent_files.log`
- **Location**: Current working directory
- **Content**: List of files with inconsistent split counts

## Usage Examples

### Standalone Executable Version Workflow:

1. **Quick Launch**:

   ```
   Double-click → launch_gui.bat
   ```
2. **Select Folder**: Click "Browse" to select image folder
3. **Configure Parameters**:

   - Check "Auto-use calculated split count" (recommended)
   - Select file format: .jpg (default)
   - Exclude string: _split_ (default)
4. **Start Processing**: Click "Start Processing" and observe progress
5. **View Results**: Check `filename_split_1.jpg` etc. split files in original folder

### Command-line Version Examples:

#### Example 1: Basic Usage

```bash
python imageCutter.py --folder_path "D:\images" --num_splits 3
```

#### Example 2: Auto Split

```bash
python imageCutter.py --folder_path "D:\images" --num_splits 3 --auto_split
```

#### Example 3: Processing PNG Files

```bash
python imageCutter.py --folder_path "D:\images" --num_splits 3 --suffix ".png"
```

## Important Notes

1. **Memory Usage**: Program loads multiple images simultaneously for processing, ensure sufficient memory
2. **Disk Space**: Split files multiply in quantity, ensure sufficient disk space
3. **File Overwriting**: Program won't overwrite existing split files, automatically skips them
4. **Thread Count**: Program automatically adjusts thread pool size based on CPU core count
5. **Image Formats**: Supports all PIL-processable image formats, JPEG and PNG recommended

## Troubleshooting

### Standalone Executable Version Issues

**Q: No interface appears after program launch?**
A:

1. Check if antivirus software is blocking program execution
2. Try running `启动图像切割器_GUI.bat` as administrator
3. Ensure system has latest Visual C++ runtime libraries installed

**Q: "Executable file not found" error?**
A:

1. Confirm `dist/ImageCutter_GUI.exe` file exists
2. If file is missing, run `构建图像切割器_GUI.bat` to rebuild

**Q: Program runs slowly or crashes?**
A:

1. Close other memory-intensive programs
2. Ensure at least 4GB available memory
3. Move image files to local hard drive (avoid network drives)

### General Issues

**Q: Program reports invalid path?**
A: Check if folder path is correct, use double quotes for paths containing spaces.

**Q: Split image quality degradation?**
A: Program uses high-quality settings by default (JPEG quality 95%), adjust `save_params` in source code if needed.

**Q: Slow processing speed?**
A: Program is already optimized with multi-threading, speed depends on CPU core count and disk I/O performance.

**Q: Insufficient memory?**
A: For very large images, may need to adjust `Image.MAX_IMAGE_PIXELS` limit or increase system memory.

## Version History

### v1.2.0 - Standalone Executable GUI Version (August 29, 2025)

- **New Features**:
  - Added standalone executable `ImageCutter_GUI.exe` (28MB)
  - No Python environment required, one-click launch
  - Quick launch script `启动图像切割器_GUI.bat`
  - Auto-build script `构建图像切割器_GUI.bat`
  - Complete README documentation and usage instructions
- **Performance Optimizations**:
  - Optimized dependencies, reduced file size
  - Improved startup speed and memory usage
  - Enhanced error handling and user prompts
- **Technical Upgrades**:
  - Built with PyInstaller 6.11.1
  - Python 3.10.11 and Conda environment
  - Optimized .spec configuration file

### v1.2.0 - GUI Version (August 29, 2025)

- **New Features**:
  - Intuitive graphical user interface
  - Real-time progress monitoring and log display
  - Folder browser and parameter validation
  - Multi-threading processing and stop functionality
  - Fully compatible with original command-line functionality

### CLI v1.0.1 - Command-line Optimized Version (December 11, 2024)

- Fixed inability to save log files
- Enhanced exception handling mechanisms
- Improved resource management and variable scoping
- Added parameter validation

### CLI v1.0.0 - Initial Version (December 10, 2024)

- Basic image splitting functionality
- Automatic optimal split count calculation
- Multi-threading processing support

## Related Documentation

- **[imageCutter_gui_simple.spec](./imageCutter_gui_simple.spec)** - PyInstaller build configuration
- **[requirements.txt](./requirements.txt)** - Python dependencies list
- **[inconsistent_files.log](./inconsistent_files.log)** - Processing log file

## Contributing

Issues and Pull Requests are welcome!

### Development Environment Setup

```bash
# Clone project
git clone https://github.com/Kai-FnLock/GMAS_Scripts.git
cd GMAS_Scripts/ImageCutter

# Install dependencies
pip install -r requirements.txt

# Run GUI version
python imageCutter_gui.py
```

### Build Executable

```bash
# Use batch script
build_gui.bat

# Or manual build
pyinstaller imageCutter_gui_simple.spec
```

## License

**Full Copyright** - All rights reserved

## Contact

- **Author**: Kai Cao
- **Email**: caokai_cgs@163.com
- **Project**: [GMAS_Scripts/ImageCutter](https://github.com/Kai-FnLock/GMAS_Scripts)

---

If this project helps you, please give it a star!
