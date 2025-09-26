# Example 5: Custom Functions

Demonstrates custom Python functions for business-specific processing.

## Custom Functions

- `business_extractor.py` - Extract client and document metadata
- `intelligent_template.py` - Create hierarchical directory structure  
- `compliance_converter.py` - Apply industry compliance rules

## Sample Files

```
ACME_CORP_legal_contract_draft_20240315.txt → Legal/ACME-CORP/2024-Q1/Contract-Draft.txt
initech_hr_policy_v2.1_final.txt → HR/INITECH/2024-Q1/Policy-Final-v02.1.txt
```

## Commands

### Using Custom Functions
```bash
python ../../main.py --input-folder sample_files \
    --extractor business_extractor.py,extract_business_document \
    --template intelligent_template.py,format_business_filename \
    --preview
```

### Full Custom Pipeline
```bash
python ../../main.py --input-folder sample_files \
    --extractor business_extractor.py,extract_business_document \
    --converter compliance_converter.py,apply_compliance_rules \
    --template intelligent_template.py,format_business_filename \
    --preview
```
