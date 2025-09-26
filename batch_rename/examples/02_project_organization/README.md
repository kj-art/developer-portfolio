# Example 2: Project File Organization

Organize project files with date normalization and structured directories.

## Sample Files

```
ProjectAlpha_Phase1_20240115_v1.2.txt → Alpha/Phase1/2024-01-15_Phase1_v1.2.txt
ProjectBeta-Phase2-2024-02-20-v2.1.txt → Beta/Phase2/2024-02-20_Phase2_v2.1.txt
```

## Commands

### Preview Changes
```bash
python ../../main.py --input-folder sample_files \
    --extractor split,"[_-]",project,phase,date,version_or_extra \
    --converter strip_prefix,project,project \
    --converter case,phase,title \
    --template stringsmith,"{{project}}/{{phase}}/{{date}}_{{phase}}_{{version_or_extra}}" \
    --preview
```

Note: This example demonstrates date handling and directory structure creation.
