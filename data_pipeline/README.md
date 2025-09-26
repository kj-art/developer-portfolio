# Multi-File Data Processing Pipeline

**Enterprise-grade data processing system with streaming optimization and intelligent schema detection**

Automatically merges and normalizes data from multiple file formats (CSV, Excel, JSON) into clean, standardized datasets. Designed for business environments where data comes from disparate sources with inconsistent naming conventions and formats.

## Key Features

- **Memory-Efficient Streaming**: Processes large datasets without loading everything into memory
- **Intelligent Schema Detection**: Automatically normalizes column names and infers unified data types
- **Flexible Index Management**: Configurable indexing strategies for different business needs
- **Professional Error Recovery**: Robust handling of malformed files and missing data
- **Cross-Format Support**: CSV, Excel (single/multi-sheet), and JSON with nested structure handling
- **Production Logging**: Comprehensive operation tracking with rich formatting

## Quick Start

### Command Line Interface
```bash
# Basic usage - merge all files in a folder
python -m data_pipeline.ui.cli --input-folder ./data --output-file merged.csv

# Advanced processing with options
python -m data_pipeline.ui.cli \
  --input-folder ./customer_data \
  --output-file consolidated_customers.xlsx \
  --recursive \
  --filetype csv xlsx \
  --index-mode sequential \
  --columns first_name,last_name,email,registration_date
```

### Graphical Interface
```bash
# Launch GUI for visual configuration
python -m data_pipeline.ui.gui
```

### Python API
```python
from data_pipeline.core.processor import DataProcessor
from data_pipeline.core.processing_config import ProcessingConfig

# Configure processing
config = ProcessingConfig(
    input_folder='./data',
    output_file='merged.csv',
    recursive=True,
    file_type_filter=['csv', 'xlsx'],
    force_in_memory=False  # Use streaming for large datasets
)

# Process files
processor = DataProcessor()
result = processor.run(config)

print(f"Processed {result.files_processed} files")
print(f"Total rows: {result.total_rows}")
print(f"Processing time: {result.processing_time:.2f}s")
```

## Business Use Cases

### Data Migration & Consolidation
Merge customer data from multiple systems during platform migrations:
```bash
python -m data_pipeline.ui.cli \
  --input-folder ./migration_data \
  --output-file customers_consolidated.csv \
  --schema customer_schema.json \
  --index-mode sequential
```

### Report Consolidation
Combine quarterly reports from different departments:
```bash
python -m data_pipeline.ui.cli \
  --input-folder ./q4_reports \
  --output-file q4_consolidated.xlsx \
  --recursive \
  --filetype xlsx \
  --to-lower --spaces-to-underscores
```

### ETL Preprocessing
Clean and standardize raw data before warehouse loading:
```bash
python -m data_pipeline.ui.cli \
  --input-folder ./raw_exports \
  --output-file warehouse_ready.csv \
  --columns customer_id,first_name,last_name,email,created_date \
  --index-mode none
```

## Processing Strategies

The system automatically selects the optimal processing strategy based on your configuration:

### Streaming Processing (Default for CSV Output)
- **Memory Usage**: Constant, regardless of dataset size
- **Performance**: Excellent for large datasets
- **Limitations**: No complex transformations requiring full dataset access

### In-Memory Processing (Default for Excel/JSON Output)
- **Memory Usage**: Loads complete dataset
- **Performance**: Fast for smaller datasets, enables complex operations
- **Capabilities**: Full pandas functionality, complex transformations

Force a specific strategy:
```bash
# Force streaming (memory-efficient)
python -m data_pipeline.ui.cli --input-folder ./data --force-streaming

# Force in-memory (full functionality)
python -m data_pipeline.ui.cli --input-folder ./data --force-in-memory
```

## Schema Management

### Automatic Schema Detection
The system automatically:
- Samples files to detect column names and types
- Normalizes column names (spaces→underscores, lowercase)
- Infers unified data types across files
- Handles name splitting (full_name → first_name + last_name)

### Custom Schema Mapping
Define custom column mappings with JSON schema files:

```json
{
  "customer_name": {
    "aliases": ["full_name", "name", "customer"],
    "type": "string"
  },
  "email_address": {
    "aliases": ["email", "e_mail", "contact_email"],
    "type": "string"
  },
  "registration_date": {
    "aliases": ["created", "signup_date", "reg_date"],
    "type": "datetime64[ns]"
  }
}
```

Usage:
```bash
python -m data_pipeline.ui.cli \
  --input-folder ./data \
  --schema custom_mappings.json \
  --output-file normalized.csv
```

## Index Management

Configure how row indices are handled in the output:

### Index Modes
- **`none`**: No index column (cleanest output)
- **`local`**: Per-file indices (0,1,2 then 0,1,2 for next file)
- **`sequential`**: Continuous indices across all files (0,1,2,3,4...)

### Examples
```bash
# No index column
python -m data_pipeline.ui.cli --input-folder ./data --index-mode none

# Sequential numbering starting from 1000
python -m data_pipeline.ui.cli --input-folder ./data --index-mode sequential --index-start 1000

# Per-file numbering starting from 1
python -m data_pipeline.ui.cli --input-folder ./data --index-mode local --index-start 1
```

## Advanced Configuration

### File Type Filtering
```bash
# Process only CSV files
python -m data_pipeline.ui.cli --input-folder ./data --filetype csv

# Process CSV and Excel files
python -m data_pipeline.ui.cli --input-folder ./data --filetype csv xlsx

# Process all supported types (default)
python -m data_pipeline.ui.cli --input-folder ./data
```

### Column Normalization Control
```bash
# Disable lowercase conversion
python -m data_pipeline.ui.cli --input-folder ./data --no-to-lower

# Disable space-to-underscore conversion
python -m data_pipeline.ui.cli --input-folder ./data --no-spaces-to-underscores

# Disable both normalizations
python -m data_pipeline.ui.cli --input-folder ./data --no-to-lower --no-spaces-to-underscores
```

### Pandas Parameter Pass-Through
Pass any pandas read/write parameters directly:

```bash
# CSV with semicolon separator and specific encoding
python -m data_pipeline.ui.cli \
  --input-folder ./data \
  --sep ";" \
  --encoding "latin-1"

# Excel with specific sheet and custom NA values
python -m data_pipeline.ui.cli \
  --input-folder ./data \
  --sheet-name "Data" \
  --na-values "NULL" "N/A" "Missing"

# Different settings for read vs write
python -m data_pipeline.ui.cli \
  --input-folder ./data \
  --encoding "utf-8" "latin-1"  # read utf-8, write latin-1
```

## Error Handling & Recovery

The system handles common data issues gracefully:

### File-Level Errors
- **Corrupted files**: Logged and skipped, processing continues
- **Permission errors**: Clear error messages with suggested fixes
- **Unsupported formats**: Automatic format detection with warnings

### Data-Level Issues
- **Missing columns**: Automatically filled with appropriate defaults
- **Type mismatches**: Intelligent type promotion (int→float→object)
- **Encoding problems**: Automatic encoding detection and conversion

### Recovery Strategies
```bash
# Verbose error reporting
python -m data_pipeline.ui.cli --input-folder ./data --verbose

# Continue processing despite errors
python -m data_pipeline.ui.cli --input-folder ./data --ignore-errors

# Strict mode (stop on first error)
python -m data_pipeline.ui.cli --input-folder ./data --strict
```

## Performance Optimization

### Memory Management
- **Streaming processing**: Constant memory usage regardless of dataset size
- **Chunk-based processing**: Configurable chunk sizes for memory/speed tradeoffs
- **Automatic garbage collection**: Proactive memory cleanup during processing

### Speed Optimization
- **Schema caching**: Pre-detected schemas speed up subsequent processing
- **Parallel file reading**: Multiple files processed concurrently when possible
- **Optimized pandas operations**: Efficient data type inference and conversion

### Monitoring
```bash
# Enable memory monitoring
python -m data_pipeline.ui.cli --input-folder ./data --monitor-memory

# Performance profiling
python -m data_pipeline.ui.cli --input-folder ./data --profile
```

## Output Formats

### CSV Output (Streaming Optimized)
```bash
python -m data_pipeline.ui.cli \
  --input-folder ./data \
  --output-file results.csv \
  --sep "," \
  --na-rep "NULL"
```

### Excel Output (Rich Formatting)
```bash
python -m data_pipeline.ui.cli \
  --input-folder ./data \
  --output-file results.xlsx \
  --sheet-name "Consolidated Data"
```

### JSON Output (Structured Data)
```bash
python -m data_pipeline.ui.cli \
  --input-folder ./data \
  --output-file results.json \
  --orient "records"
```

### Console Output
```bash
# Preview data without saving
python -m data_pipeline.ui.cli --input-folder ./data
```

## Integration Examples

### CI/CD Pipeline Integration
```yaml
# .github/workflows/data-processing.yml
- name: Process Customer Data
  run: |
    python -m data_pipeline.ui.cli \
      --input-folder ./raw_data \
      --output-file ./processed/customers.csv \
      --schema ./schemas/customer.json \
      --index-mode sequential
```

### Cron Job for Regular Processing
```bash
# Process daily exports at 2 AM
0 2 * * * /usr/bin/python3 -m data_pipeline.ui.cli \
  --input-folder /data/daily_exports \
  --output-file /data/processed/daily_$(date +\%Y\%m\%d).csv \
  --recursive --force-streaming
```

### Docker Container Usage
```dockerfile
FROM python:3.9-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
ENTRYPOINT ["python", "-m", "data_pipeline.ui.cli"]
```

```bash
# Run in container
docker run -v /data:/data data-pipeline \
  --input-folder /data/input \
  --output-file /data/output/merged.csv
```

## API Reference

### ProcessingConfig
```python
@dataclass
class ProcessingConfig:
    input_folder: str                              # Required: source directory
    output_file: Optional[str] = None              # Output path (None = console)
    recursive: bool = False                        # Search subdirectories
    file_type_filter: Optional[List[str]] = None   # ['csv', 'xlsx', 'json']
    schema_map: Optional[Dict] = None              # Custom column mappings
    to_lower: bool = True                          # Lowercase column names
    spaces_to_underscores: bool = True             # Convert spaces in names
    index_mode: Optional[IndexMode] = None         # Index handling strategy
    index_start: int = 0                           # Starting index value
    columns: Optional[List[str]] = None            # Expected columns
    force_in_memory: bool = False                  # Override streaming
    read_options: Dict = field(default_factory=dict)   # Pandas read options
    write_options: Dict = field(default_factory=dict)  # Pandas write options
```

### DataProcessor
```python
class DataProcessor:
    def __init__(self, read_kwargs: dict = None, write_kwargs: dict = None)
    def run(self, config: ProcessingConfig) -> ProcessingResult
    def get_available_strategies(self) -> List[str]
    def get_service_status(self) -> Dict
```

### ProcessingResult
```python
@dataclass
class ProcessingResult:
    files_processed: int        # Number of files successfully processed
    total_rows: int            # Total rows in output
    total_columns: int         # Number of columns in output
    processing_time: float     # Processing duration in seconds
    output_file: Optional[str] # Path to output file
    schema: Optional[Dict]     # Detected/applied schema
    data: Optional[DataFrame]  # Complete dataset (in-memory mode only)
```

## Architecture

### Design Principles
- **Strategy Pattern**: Automatic selection of streaming vs in-memory processing
- **Service-Oriented**: Modular components for schema detection, file processing, output writing
- **Configuration-Driven**: Flexible behavior without code changes
- **Producer-Consumer**: Clean separation between data generation and consumption

### Component Overview
```
DataProcessor (Orchestrator)
├── SchemaDetector (Service)
├── FileProcessor (Service)  
├── OutputWriter (Service)
├── StreamingProcessor (Strategy)
├── InMemoryProcessor (Strategy)
└── IndexManager (Utility)
```

### Extension Points
- **Custom file handlers**: Support new file formats
- **Custom schema detectors**: Advanced schema inference
- **Custom output writers**: New output formats
- **Custom processing strategies**: Specialized processing logic

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m data_pipeline.ui.cli --help
```

### Requirements
- **Python**: 3.7+
- **Core**: pandas, openpyxl
- **Optional**: psutil (memory monitoring), rich (enhanced progress)

## Troubleshooting

### Common Issues

**Memory errors with large files:**
```bash
# Use streaming processing
python -m data_pipeline.ui.cli --input-folder ./data --output-file results.csv
```

**Encoding issues:**
```bash
# Specify encoding explicitly  
python -m data_pipeline.ui.cli --input-folder ./data --encoding "utf-8"
```

**Schema conflicts:**
```bash
# Use predefined columns to skip detection
python -m data_pipeline.ui.cli --input-folder ./data --columns "id,name,email,date"
```

**Performance issues:**
```bash
# Enable monitoring to identify bottlenecks
python -m data_pipeline.ui.cli --input-folder ./data --monitor-memory --profile
```

### Getting Help
```bash
# Comprehensive help including pandas options
python -m data_pipeline.ui.cli --help

# Show version and capabilities
python -m data_pipeline.ui.cli --version

# Test with sample data
python -m data_pipeline.ui.cli --input-folder ./test_data --verbose
```

---

**Data Processing Pipeline** demonstrates enterprise-level data engineering capabilities with production-ready error handling, memory optimization, and flexible configuration. Perfect for data migration projects, ETL preprocessing, and business intelligence workflows.

*Part of the [Automation Engineering Portfolio](../) showcasing scalable data processing solutions.*