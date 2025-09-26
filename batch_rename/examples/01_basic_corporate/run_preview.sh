#!/bin/bash
# Preview script for basic corporate document standardization

echo "=== Batch Rename Tool - Basic Corporate Preview ==="
echo "This will show you what changes would be made WITHOUT actually renaming files."
echo

python ../../main.py --input-folder sample_files \
    --extractor split,"[ _-]",dept,doc_type,extra1,extra2,extra3 \
    --converter case,dept,upper \
    --converter case,doc_type,upper \
    --converter case,extra1,upper \
    --converter case,extra2,upper \
    --converter case,extra3,upper \
    --template join,dept,doc_type,extra1,extra2,extra3,separator=- \
    --preview

echo
echo "=== Preview Complete ==="
echo "If the changes look good, run ./run_execute.sh to apply them."
