# GMAS Scripts

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/Version-1.1-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![GMAS](https://img.shields.io/badge/GMAS-Geological%20Scripts-orange)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Rights](https://img.shields.io/badge/Rights-All%20Rights%20Reserved-red)

A collection of Python scripts and tools for geological data processing, image analysis, and spectral library management.

## Projects Overview

### Daily Data Collection

> [DailyDataCollection/](DailyDataCollection/)

A comprehensive data collection and processing system for GMAS project that handles daily KMZ files, monitoring, parsing, and report generation.

**Key Features:**
- Monitor and collect KMZ files from WeChat folders automatically
- Parse KMZ files and extract daily observation points for summary reports
- Convert processed data to Microsoft Excel format
- Combine multiple KMZ files into unified datasets
- Generate PDF maps using ArcPy integration

**Documentation:** See [DailyDataCollection/README.md](DailyDataCollection/README.md) for detailed information.

### Image Cutter

> [ImageCutter/](ImageCutter/)

An automated image segmentation tool designed for processing scanned thin-section images with intelligent calculation capabilities.

**Key Features:**
- Automatic calculation of optimal segmentation parameters
- Multi-threaded processing with thread pool executor
- GUI and command-line interfaces available
- Quality preservation for JPEG and PNG formats
- Standalone executable version (no Python installation required)

**Documentation:** See [ImageCutter/README.md](ImageCutter/README.md) for detailed usage instructions.

### Colour Tune

> [ColourTune/](ColourTune/)

Color adjustment and calibration utilities for geological image processing and analysis.

### Spectral Library

> [SpectralLibrary/](SpectralLibrary/)

Tools and utilities for spectral data management and mineral identification.

**Components:**
- `FilePicker/`: File filtering and organization scripts
- `SampleRecognition/`: Sample identification and analysis tools

## Quick Start

1. **Install Dependencies**  
   Python 3.10 is recommended. Install required packages including GDAL, openpyxl, lxml, watchdog, and tabulate.

   ```sh
   pip install -r requirements.txt
   ```

2. **Configure Parameters**  
   Modify [DailyDataCollection/config.py](DailyDataCollection/config.py) to match your local paths and settings.

3. **Run Main Program**  
   ```sh
   python -m DailyDataCollection
   ```

4. **Check Output**  
   - Daily reports and statistics are generated in the specified `WORKSPACE` directory
   - Log output is displayed in the console

## Design and Extension

- KMZ/KML parsing and construction details: [DailyDataCollection/Design/](DailyDataCollection/Design/)
- Support for custom KML Schema, compatible with KML 2.2/2.3
- Extensible architecture for additional geospatial data processing, report formats, and automation workflows

## Testing and Contribution

- Unit tests are located in `DailyDataCollection/tests/`
- Pull requests and issues are welcome