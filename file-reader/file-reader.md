---
name: file-reader
version: 1.0.0
description: >
  Use this skill when the user wants to read, process, and convert Office files (Word, Excel, PowerPoint) and PDF files. 
  Supports content analysis, information extraction, format conversion, and report generation. 
  Outputs can be the original file content, processed data, or analysis reports.
triggers:
  keywords: ["读取文件", "读取office", "读取pdf", "文件处理", "file reader", "read file", "process file", "convert file"]
  file_extensions: [".docx", ".xlsx", ".pptx", ".pdf", ".txt", ".md"]
platform: [windows]
---

# File Reader — Office 和 PDF 文件读取器

## Overview

This skill enables reading, processing, and converting Office files (Word, Excel, PowerPoint) and PDF files. It provides capabilities for content analysis, information extraction, format conversion, and report generation. Designed for Windows environments with Trae AI.

## Prerequisites / Setup

### Environment Requirements
- Python 3.9+
- Required packages:
  - `python-docx` (for Word files)
  - `openpyxl` (for Excel files)
  - `python-pptx` (for PowerPoint files)
  - `PyPDF2` (for PDF files)
  - `pandas` (for data analysis)

### Installation Steps
1. Open PowerShell in the `file-reader/scripts` directory
2. Run: `python setup_env.py`
3. Verify installation: `python file_reader.py --action check-env`

## Decision Tree

### User Intent Analysis
1. **File type detection** → Determine which parser to use based on file extension
2. **Processing request** → Identify if user wants content extraction, analysis, or conversion
3. **Output format** → Determine whether to output to console, generate new file, or create report

## Core Workflows

### Workflow 1: Read and Display File Content

**Steps:**
1. **Step 0: Locate script**
   ```powershell
   # Find the script path
   $scriptPath = Get-ChildItem -Recurse -Name "file_reader.py" | Select-Object -First 1
   $scriptDir = Split-Path -Parent $scriptPath
   ```

2. **Step 1: Read file**
   ```powershell
   python "$scriptPath" --action read --file-path "C:\path\to\file.docx"
   ```

3. **Step 2: Display content**
   - For text files: Show content directly
   - For Excel files: Show sheet names and sample data
   - For PDF files: Show extracted text

### Workflow 2: Analyze File Content

**Steps:**
1. **Step 1: Read and analyze**
   ```powershell
   python "$scriptPath" --action analyze --file-path "C:\path\to\file.xlsx"
   ```

2. **Step 2: Generate report**
   - For Excel: Basic statistics, column analysis
   - For Word: Word count, paragraph analysis
   - For PDF: Text extraction and basic analysis

### Workflow 3: Convert File Format

**Steps:**
1. **Step 1: Convert file**
   ```powershell
   python "$scriptPath" --action convert --file-path "C:\path\to\file.pdf" --output-format "txt"
   ```

2. **Step 2: Save output**
   - Output file will be saved in the same directory as the original file

## Parameter Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--action` | Yes | Action to perform: read, analyze, convert, check-env, locate |
| `--file-path` | Yes | Path to the file to process |
| `--output-format` | No | Output format for conversion (txt, md, csv) |
| `--output-path` | No | Custom output path for converted files |

## Error Handling

### Error Mapping Table

| Error | Possible Cause | Recovery Action |
|-------|---------------|----------------|
| `ModuleNotFoundError: No module named 'python-docx'` | Missing dependency | Run `python setup_env.py` to install required packages |
| `FileNotFoundError: [Errno 2] No such file or directory` | Invalid file path | Check the file path and ensure the file exists |
| `PermissionError: [Errno 13] Permission denied` | Insufficient permissions | Run PowerShell as administrator or check file permissions |
| `Unsupported file format` | File type not supported | Check if the file extension is in the supported list |
| `PDFReadError: Could not read PDF file` | Corrupted PDF file | Try with a different PDF file or repair the current one |

### Error Recovery Workflow

1. **Dependency errors** → Run `python file_reader.py --action check-env` to diagnose
2. **File errors** → Verify file path and permissions
3. **Format errors** → Check if file type is supported
4. **Unknown errors** → Run with `--action check-env` and check console output

## Complete Examples

### Example 1: Read Word Document

**User:** "帮我读取这份Word文档"

**Steps:**
1. **Step 1: Locate script**
   ```powershell
   $scriptPath = Get-ChildItem -Recurse -Name "file_reader.py" | Select-Object -First 1
   ```

2. **Step 2: Read file**
   ```powershell
   python "$scriptPath" --action read --file-path "C:\Documents\报告.docx"
   ```

**Expected Output:**
```
📄 File: C:\Documents\报告.docx
📊 Word document with 5 paragraphs

Content preview:
================
这是一份测试报告，包含了项目的基本信息和分析结果。

项目名称：文件读取器
项目类型：AI Skill
...
```

### Example 2: Analyze Excel File

**User:** "分析这份Excel数据并生成报告"

**Steps:**
1. **Step 1: Locate script**
   ```powershell
   $scriptPath = Get-ChildItem -Recurse -Name "file_reader.py" | Select-Object -First 1
   ```

2. **Step 2: Analyze file**
   ```powershell
   python "$scriptPath" --action analyze --file-path "C:\Data\销售数据.xlsx"
   ```

**Expected Output:**
```
📄 File: C:\Data\销售数据.xlsx
📊 Excel file with 2 sheets

Sheet: 销售数据
- Rows: 100
- Columns: 5
- Columns: 日期, 产品, 销售额, 数量, 地区

Basic Statistics:
- 总销售额: ¥1,234,567
- 平均销售额: ¥12,345
- 最高销售额: ¥50,000
- 最低销售额: ¥1,000

Top 5 products by sales:
1. 产品A: ¥250,000
2. 产品B: ¥200,000
3. 产品C: ¥180,000
4. 产品D: ¥150,000
5. 产品E: ¥120,000
```

## Platform-Specific Notes

### Windows Notes
- **Path handling:** Use double quotes around file paths with spaces
- **Encoding:** Office files use UTF-8 encoding by default
- **Permissions:** Run PowerShell as administrator if accessing system files
- **Python path:** Ensure Python 3.9+ is in PATH

## Known Pitfalls

- **Large files:** Processing very large files may take time and memory
- **Complex Excel files:** Files with macros or complex formulas may not be fully supported
- **Scanned PDFs:** OCR is not included; scanned PDFs may not yield good results
- **File locks:** Ensure files are not open in other applications when processing

## Notes

- **Supported file types:** .docx, .xlsx, .pptx, .pdf, .txt, .md
- **Output limits:** Large file content may be truncated in the console
- **Performance:** Processing time depends on file size and complexity
- **Security:** Does not execute macros or embedded code in Office files

## Negative Instructions

> [!IMPORTANT]
> - Do NOT process files larger than 100MB to avoid memory issues
> - Do NOT execute macros or embedded code in Office files
> - Do NOT read system files or sensitive documents without user permission
> - Do NOT modify the original files; always work on copies when converting
> - Do NOT share file contents with third-party services without user consent
