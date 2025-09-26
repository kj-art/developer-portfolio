# Batch Rename Tool - Examples

Comprehensive examples demonstrating the batch rename tool's capabilities.

## Examples

1. **01_basic_corporate/** - Simple business document standardization
2. **02_project_organization/** - Project file management with dates  
3. **05_custom_functions/** - Custom Python function examples
4. **06_bulk_processing/** - Large dataset scenarios

## Quick Start

```bash
# Test basic example
cd 01_basic_corporate
./run_preview.sh

# Test custom functions  
cd ../05_custom_functions
python ../../main.py --input-folder sample_files --extractor business_extractor.py,extract_business_document --template intelligent_template.py,format_business_filename --preview
```

## Learning Path

Start with 01_basic_corporate for fundamentals, then progress through examples to build complexity.
