import sys
import csv
from typing import List, Dict, Tuple, Optional

#!/usr/bin/env python3
"""
CapstoneProject.py

CSV-Based Student Performance Analyzer

Reads a CSV of student rows (Name, Subject, Marks), validates rows,
creates a cleaned CSV with validation info, and a summary CSV with
average marks per student.

Usage:
    python CapstoneProject.py input.csv
If no input is provided, defaults to 'students.csv'.

Only uses Python standard library.
"""



def read_csv_rows(path: str) -> List[Dict[str, str]]:
    """
    Read CSV and return list of rows as dicts with keys 'Name', 'Subject', 'Marks'.
    If headers are missing or different, attempt a best-effort mapping from first 3 columns.
    """
    rows = []
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                first = next(reader)
            except StopIteration:
                return []
            # Normalize header names if they look like headers
            headers = [h.strip() for h in first]
            expected = ['name', 'subject', 'marks']
            if len(headers) >= 3 and all(h.lower() in expected for h in headers[:3]):
                # Use DictReader with original file pointer reset
                f.seek(0)
                dict_reader = csv.DictReader(f)
                for r in dict_reader:
                    rows.append({
                        'Name': r.get('Name', r.get('name', '')).strip(),
                        'Subject': r.get('Subject', r.get('subject', '')).strip(),
                        'Marks': r.get('Marks', r.get('marks', '')).strip()
                    })
            else:
                # Treat first row as data and map first three columns
                rows.append({
                    'Name': headers[0].strip(),
                    'Subject': headers[1].strip() if len(headers) > 1 else '',
                    'Marks': headers[2].strip() if len(headers) > 2 else ''
                })
                for cols in reader:
                    rows.append({
                        'Name': cols[0].strip() if len(cols) > 0 else '',
                        'Subject': cols[1].strip() if len(cols) > 1 else '',
                        'Marks': cols[2].strip() if len(cols) > 2 else ''
                    })
    except FileNotFoundError:
        raise
    return rows


def validate_mark(mark_str: str) -> Tuple[bool, Optional[float], str]:
    """
    Validate a mark string.
    Returns (is_valid, numeric_value_or_None, error_message).
    Valid marks are numeric (int/float) in range 0..100 inclusive.
    """
    if mark_str is None:
        return False, None, 'Missing Marks'
    s = mark_str.strip()
    if s == '':
        return False, None, 'Missing Marks'
    try:
        # allow integers or floats
        val = float(s)
    except ValueError:
        return False, None, 'Invalid Marks'
    if not (0 <= val <= 100):
        return False, None, 'Marks Out of Range'
    return True, val, ''


def process_rows(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Dict[str, Dict[str, object]]]:
    """
    Validate each row and prepare cleaned rows list.
    Also build per-student aggregation dict for summary.
    Returns (cleaned_rows, student_summary_data)
    student_summary_data[name] -> {'valid_marks': [...], 'invalid_count': int}
    """
    cleaned = []
    students: Dict[str, Dict[str, object]] = {}
    for r in rows:
        name = r.get('Name', '').strip()
        subject = r.get('Subject', '').strip()
        marks = r.get('Marks', '')
        row_status = 'Valid'
        error = ''
        is_valid, value, error_msg = validate_mark(marks)
        if not name:
            row_status = 'Invalid'
            error = 'Missing Name'
            # if name missing, group under empty string key
            student_key = ''
        else:
            student_key = name
        if not subject:
            # subject optional for aggregation, but flag if missing
            if row_status == 'Valid':
                row_status = 'Invalid'
                error = 'Missing Subject'
            else:
                error = (error + '; Missing Subject').strip('; ')
        if is_valid and row_status == 'Valid':
            # mark is valid and other fields present
            students.setdefault(student_key, {'valid_marks': [], 'invalid_count': 0})
            students[student_key]['valid_marks'].append(value)
        else:
            # invalid mark or other invalidity
            students.setdefault(student_key, {'valid_marks': [], 'invalid_count': 0})
            students[student_key]['invalid_count'] += 1
            if error == '':
                error = error_msg
            row_status = 'Invalid'
        cleaned.append({
            'Name': name,
            'Subject': subject,
            'Marks': marks,
            'Status': row_status,
            'Error': error
        })
    return cleaned, students


def write_cleaned_csv(path: str, cleaned_rows: List[Dict[str, str]]) -> None:
    """
    Write cleaned rows to CSV with columns: Name,Subject,Marks,Status,Error
    """
    fieldnames = ['Name', 'Subject', 'Marks', 'Status', 'Error']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in cleaned_rows:
            writer.writerow(r)


def write_summary_csv(path: str, students: Dict[str, Dict[str, object]]) -> None:
    """
    Write summary CSV with columns: Name,AverageMarks,Status
    Status is 'Valid' if student has at least one valid mark and no invalid rows,
    'Partial' if student has both valid and invalid rows,
    'Invalid' if student has no valid marks.
    AverageMarks is numeric rounded to 2 decimals or 'N/A' when no valid marks.
    """
    fieldnames = ['Name', 'AverageMarks', 'Status']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for name, data in sorted(students.items(), key=lambda x: (x[0] or '').lower()):
            valid_marks = data.get('valid_marks', [])
            invalid_count = data.get('invalid_count', 0)
            if valid_marks:
                avg = sum(valid_marks) / len(valid_marks)
                avg_str = f"{avg:.2f}"
                if invalid_count:
                    status = 'Partial'
                else:
                    status = 'Valid'
            else:
                avg_str = 'N/A'
                status = 'Invalid'
            writer.writerow({
                'Name': name,
                'AverageMarks': avg_str,
                'Status': status
            })


def main(argv: List[str]) -> int:
    if len(argv) >= 2:
        input_path = argv[1]
    else:
        input_path = 'students.csv'
    cleaned_out = 'cleaned_report.csv'
    summary_out = 'summary_report.csv'
    try:
        rows = read_csv_rows(input_path)
    except FileNotFoundError:
        print(f"Error: input file not found: {input_path}")
        return 1
    except Exception as e:
        print(f"Error reading file: {e}")
        return 1
    if not rows:
        print("No rows to process.")
        return 0
    cleaned, students = process_rows(rows)
    try:
        write_cleaned_csv(cleaned_out, cleaned)
        write_summary_csv(summary_out, students)
    except Exception as e:
        print(f"Error writing output files: {e}")
        return 1
    print(f"Processed {len(rows)} rows.")
    print(f"Cleaned report: {cleaned_out}")
    print(f"Summary report: {summary_out}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
