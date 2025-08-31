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

**Documentation:** 
- 📖 [Main Documentation](DailyDataCollection/README.md)
- 📖 [English Documentation](DailyDataCollection/README_en.md)
- 📖 [中文文档](DailyDataCollection/README_cn.md)

### Image Cutter

> [ImageCutter/](ImageCutter/)

An image segmentation tool designed for processing scanned thin-section images with automatic calculation capabilities.

**Key Features:**
- Automatic calculation of optimal segmentation parameters
- Multi-threaded processing with thread pool executor
- GUI and command-line interfaces available
- Quality preservation for JPEG and PNG formats
- Standalone executable version (no Python installation required)

**Documentation:** 
- 📖 [Main Documentation](ImageCutter/README.md)
- 📖 [English Documentation](ImageCutter/README_en.md)
- 📖 [中文文档](ImageCutter/README_cn.md)

### Colour Tune

> [ColourTune/](ColourTune/)

Color adjustment and calibration utilities for geological image processing and analysis.

**Documentation:** *Documentation to be added*

### Spectral Library

> [SpectralLibrary/](SpectralLibrary/)

Tools and utilities for spectral data management and mineral identification.

**Components:**
- `FilePicker/`: File filtering and organization scripts
- `SampleRecognition/`: Sample identification and analysis tools

**Documentation:** *Documentation to be added*