#!/bin/bash
# Execute script for basic corporate document standardization

echo "=== Batch Rename Tool - Basic Corporate Execution ==="
echo "⚠️  WARNING: This will actually rename your files!"
echo
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Executing rename operation..."
    
    python ../../main.py --input-folder sample_files \
        --extractor split,"[ _-]",dept,doc_type,extra1,extra2,extra3 \
        --converter case,dept,upper \
        --converter case,doc_type,upper \
        --converter case,extra1,upper \
        --converter case,extra2,upper \
        --converter case,extra3,upper \
        --template join,dept,doc_type,extra1,extra2,extra3,separator=- \
        --execute
    
    echo
    echo "=== Execution Complete ==="
else
    echo "Operation cancelled."
fi
