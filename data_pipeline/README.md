# Multi-File Data Processing Pipeline

**Enterprise-grade data processing system with streaming optimization and intelligent schema detection**

Automatically merges and normalizes data from multiple file formats (CSV, Excel, JSON) into clean, standardized datasets. Designed for business environments where data comes from disparate sources with inconsistent naming conventions and formats.

## Key Features

- **Streaming Processing**: Memory-efficient handling of large datasets with automatic CSV streaming
- **Schema Detection**: Intelligent column normalization and type inference across file formats
- **Flexible Output**: Support for CSV, Excel, and JSON output formats
- **Index Management**: Configurable indexing strategies (none, per-file, sequential)
- **Error Recovery**: Robust handling of malformed files and missing data
- **Professional Logging**: Comprehensive operation tracking with StringSmith-powered formatting

## Quick Start

### CLI Usage
```bash
# Basic usage - merge all files in a folder
python -m data_pipeline.ui.cli --input-folder ./data --output-file merged.csv

# Advanced usage with options
python -m data_pipeline.ui.cli \
  --input-folder ./data \
  --output-file results.xlsx \
  --recursive \
  --filetype csv xlsx \
  --index-mode sequential \
  --columns first_name,last_name,age,email
```

### GUI Usage
```bash
# Launch graphical interface
python -m data_pipeline.ui.gui
```

## Business Use Cases

- **Data Migration**: Consolidate customer data from multiple systems into single dataset
- **Report Consolidation**: Merge quarterly reports from different departments
- **ETL Preprocessing**: Clean and standardize raw data before warehouse loading
- **Audit Preparation**: Combine records from various sources for compliance reviews

## Architecture Highlights

**Strategy Pattern**: Automatically selects streaming vs in-memory processing based on output format and dataset size

**Service-Oriented**: Modular design with separate services for schema detection, file processing, and output writing

**Configuration-Driven**: Flexible parameter system supporting both simple and complex processing scenarios

**Production-Ready**: Comprehensive error handling, logging, and progress monitoring

## Current Status

✅ **Complete**: Core processing engine, CLI interface, schema detection  
🚧 **In Progress**: GUI interface, advanced error recovery  
🔄 **Planned**: Cloud storage integration, REST API interface

## Installation

```bash
pip install -r requirements.txt
```

## Example Output

```bash
$ python -m data_pipeline.ui.cli --input-folder ./sample_data --output-file clean_data.csv

[INFO] Data pipeline started input_folder=./sample_data
[INFO] Schema detection complete columns_detected=5 files_sampled=3
[INFO] Streaming processing complete files_processed=3 total_rows=1247 duration=0.85s
```

---

*Part of the [Automation Engineering Portfolio](../) - demonstrating enterprise data processing capabilities*