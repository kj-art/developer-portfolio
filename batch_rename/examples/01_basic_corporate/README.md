# Example 1: Basic Corporate Document Standardization

Transform inconsistent corporate filenames into standardized format.

## Sample Files

```
HR_handbook_2024.txt → HR-HANDBOOK-2024.txt
marketing-guidelines-draft.txt → MARKETING-GUIDELINES-DRAFT.txt  
IT security policy v2.txt → IT-SECURITY-POLICY-V2.txt
```

## Commands

### Preview Changes (Safe)
```bash
python ../../main.py --input-folder sample_files \
    --extractor split,"[ _-]",dept,doc_type,extra1,extra2,extra3 \
    --converter case,dept,upper \
    --converter case,doc_type,upper \
    --converter case,extra1,upper \
    --converter case,extra2,upper \
    --converter case,extra3,upper \
    --template join,dept,doc_type,extra1,extra2,extra3,separator=- \
    --preview
```

### Execute Changes
Add `--execute` instead of `--preview` to actually rename files.

## Run Scripts

- `./run_preview.sh` - Quick preview
- `./run_execute.sh` - Execute with confirmation
