#!/usr/bin/env python3
"""
Test file generator for batch rename tool.

Creates sample files with various naming patterns to test functionality.
"""

from pathlib import Path

def create_test_files():
    """Create test files and directories."""
    
    # Create test directories
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    subdirs = ["hr_docs", "finance_docs", "marketing_assets"]
    for subdir in subdirs:
        (test_dir / subdir).mkdir(exist_ok=True)
    
    # Create test files with various naming patterns
    test_files = [
        # Split-friendly patterns
        "HR_report_20240915.pdf",
        "HR_memo_20240916.docx", 
        "FINANCE_budget_Q3_2024.xlsx",
        "FINANCE_invoice_INV001.pdf",
        "MARKETING_campaign_summer.jpg",
        "MARKETING_logo_v2.png",
        
        # Files with numbers that need padding
        "PROJECT_status_1.pdf",
        "PROJECT_status_15.pdf", 
        "PROJECT_notes_2.docx",
        
        # Files with inconsistent casing
        "hr_handbook_final.pdf",
        "Finance_Report_draft.xlsx",
        "marketing_Brief_v1.docx",
        
        # Files that might cause collisions
        "DEPT_doc_1.pdf",
        "DEPT_document_1.pdf",  # Both could become dept_doc_1.pdf
        
        # Files to potentially filter out
        "temp_file.tmp",
        "backup_data_old.bak",
        "small_image.jpg",  # Will be small
        "large_video.mp4",  # Will be large
    ]
    
    # Create the actual files
    for filename in test_files:
        file_path = test_dir / filename
        
        # Create files with different sizes for testing size filters
        if "small" in filename:
            content = b"small file content"
        elif "large" in filename or filename.endswith(".mp4"):
            content = b"x" * (2 * 1024 * 1024)  # 2MB file
        else:
            content = f"Test content for {filename}".encode()
        
        file_path.write_bytes(content)
        print(f"Created: {file_path}")
    
    # Create some files in subdirectories for recursive testing
    subdir_files = [
        ("hr_docs", "employee_handbook_2024.pdf"),
        ("hr_docs", "policy_update_v3.docx"),
        ("finance_docs", "Q3_expenses_final.xlsx"),
        ("marketing_assets", "hero_image_1920x1080.jpg"),
    ]
    
    for subdir, filename in subdir_files:
        file_path = test_dir / subdir / filename
        content = f"Test content for {filename} in {subdir}".encode()
        file_path.write_bytes(content)
        print(f"Created: {file_path}")
    
    print(f"\nTest setup complete! Created {len(test_files)} files in test_files/")
    print("Plus additional files in subdirectories for recursive testing.")
    
    # Print some example commands to try
    print("\n" + "="*60)
    print("EXAMPLE COMMANDS TO TRY:")
    print("="*60)
    
    print("\n1. Basic split extraction with number padding:")
    print("python main.py \\")
    print("  --input-folder ./test_files \\")
    print("  --extractor split,_,dept,type,date \\")
    print("  --converter pad_numbers,date,4 \\")
    print("  --converter template,\"{dept}_{type}_{date}\" \\")
    print("  --preview")
    
    print("\n2. Filter for PDFs only, pad numbers:")
    print("python main.py \\")
    print("  --input-folder ./test_files \\")
    print("  --filter file-type \\")
    print("  --filter-args \"pdf\" \\")
    print("  --extractor split \\")
    print("  --extractor-args \"split_on=_,fields=project,type,num\" \\")
    print("  --converter pad_numbers \\")
    print("  --converter-args \"field=num,width=3\" \\")
    print("  --template \"{project}_{type}_{num}\" \\")
    print("  --preview")
    
    print("\n3. Exclude backup/temp files, include large files only:")
    print("python main.py \\")
    print("  --input-folder ./test_files \\")
    print("  --filter !pattern,file-size \\")
    print("  --filter-args \"*.tmp,*.bak\",\"min=1MB\" \\")
    print("  --extractor split \\")
    print("  --extractor-args \"split_on=_,fields=type,name,version\" \\")
    print("  --converter lowercase \\")
    print("  --converter-args \"fields=type\" \\")
    print("  --template \"{type}_{name}_{version}\" \\")
    print("  --preview")
    
    print("\n4. Recursive processing with multiple filters:")
    print("python main.py \\")
    print("  --input-folder ./test_files \\")
    print("  --recursive \\")
    print("  --filter file-type,!pattern \\")
    print("  --filter-args \"pdf,docx\",\"*_old,*_backup*\" \\")
    print("  --extractor split \\")
    print("  --extractor-args \"split_on=_,fields=dept,doc,version\" \\")
    print("  --converter template \\")
    print("  --converter-args \"pattern={dept}_{doc}_{version:>10}\" \\")
    print("  --preview")

if __name__ == "__main__":
    create_test_files()