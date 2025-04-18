import csv
import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from email.utils import parseaddr
import phonenumbers

@dataclass
class ValidationError:
    file: str
    line: int
    field: str
    message: str

class SDSValidator:
    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.errors: List[ValidationError] = []
        self.data_cache: Dict[str, List[Dict[str, str]]] = {}
        self.sourcedid_cache: Dict[str, Set[str]] = {}
        self.removed_records: Dict[str, List[Dict[str, str]]] = {}
        self.output_directory = os.path.join(directory_path, 'validated_output')
        self.report_file = os.path.join(directory_path, 'validation_report.json')

    def validate_all(self) -> Tuple[List[ValidationError], str, str]:
        """Run all validations and output cleaned files and a JSON report"""
        # Reset state
        self.errors = []
        self.removed_records = {}

        # Prepare output directory
        if os.path.exists(self.output_directory):
            shutil.rmtree(self.output_directory)
        os.makedirs(self.output_directory)

        # Ensure required files are present
        self._validate_file_existence()

        # Process both required and optional files
        required = ['orgs.csv', 'users.csv', 'roles.csv']
        optional = ['classes.csv', 'enrollments.csv', 'academicSessions.csv', 'courses.csv']
        for fname in required + optional:
            path = os.path.join(self.directory_path, fname)
            if os.path.exists(path):
                self._validate_and_fix_file(fname)

        # Build and write JSON report
        report = {
            'hasErrors': len(self.errors) > 0,
            'errors': [e.__dict__ for e in self.errors],
            'removedRecords': self.removed_records
        }
        with open(self.report_file, 'w', encoding='utf-8') as rf:
            json.dump(report, rf, ensure_ascii=False, indent=2)

        return self.errors, self.output_directory, self.report_file

    def _validate_file_existence(self):
        """Ensure all required files exist"""
        for fname in ['orgs.csv', 'users.csv', 'roles.csv']:
            if not os.path.exists(os.path.join(self.directory_path, fname)):
                self.errors.append(ValidationError(
                    file=fname, line=0, field='',
                    message=f'Required file {fname} not found'
                ))

    def _validate_and_fix_file(self, filename: str):
        """Validate a single CSV and output cleaned version"""
        infile = os.path.join(self.directory_path, filename)
        outfile = os.path.join(self.output_directory, filename)

        # Expected headers for each file
        headers = {
            'orgs.csv': ['sourcedId','name','type','parentSourcedId'],
            'users.csv': ['sourcedId','username','givenName','familyName','password','activeDirectoryMatchId','email','phone','sms'],
            'roles.csv': ['userSourcedId','orgSourcedId','role','sessionSourcedId','grade','isPrimary','roleStartDate','roleEndDate'],
            'classes.csv': ['sourcedId','orgSourcedId','title','sessionSourcedIds','courseSourcedId'],
            'enrollments.csv': ['classSourcedId','userSourcedId','role'],
            'academicSessions.csv': ['sourcedId','title','type','startDate','endDate','parentSourcedId'],
            'courses.csv': ['sourcedId','orgSourcedId','title','courseCode','grades']
        }
        
        # SDS V2.1互換のヘッダー
        sds_v21_headers = {
            'roles.csv': ['sourcedId', 'userSourcedId', 'orgSourcedId', 'role', 'sessionSourcedId'],
            'enrollments.csv': ['sourcedId', 'classSourcedId', 'userSourcedId', 'role']
        }
        
        try:
            with open(infile, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                actual = reader.fieldnames or []
                
                # SDS V2.1互換の検証を追加
                header_valid = set(actual) == set(headers.get(filename, []))
                if filename in sds_v21_headers and not header_valid:
                    header_valid = set(actual) == set(sds_v21_headers[filename])
                
                if not header_valid:
                    # ファイル名に対応するヘッダーリストを決定
                    expected = headers.get(filename, [])
                    if filename in sds_v21_headers:
                        expected = f"{headers.get(filename, [])} または {sds_v21_headers[filename]}"
                    
                    self.errors.append(ValidationError(
                        file=filename, line=1, field='header',
                        message=f'Invalid header. Expected {expected}, got {actual}'
                    ))
                    return
                rows = list(reader)

            cleaned = []
            seen = set()
            removed = []
            for idx, row in enumerate(rows, start=2):
                sid = row.get('sourcedId') or row.get('classSourcedId') or ''
                # Skip duplicate checks for roles.csv and enrollments.csv
                if filename not in ['roles.csv', 'enrollments.csv'] and sid in seen:
                    # Only non-roles, non-enrollments files report duplicates
                    self.errors.append(ValidationError(
                        file=filename, line=idx, field='sourcedId',
                        message=f'Duplicate sourcedId: {sid}'
                    ))
                    removed.append(row)
                    continue
                if self._validate_record(filename, row, idx):
                    cleaned.append(row)
                    seen.add(sid)
                else:
                    removed.append(row)

            if removed:
                self.removed_records[filename] = removed

            # 使用するヘッダーを決定
            output_headers = headers.get(filename, [])
            if filename in sds_v21_headers and set(actual) == set(sds_v21_headers[filename]):
                output_headers = sds_v21_headers[filename]

            # Write cleaned CSV
            with open(outfile, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=output_headers)
                writer.writeheader()
                writer.writerows(cleaned)

            self.data_cache[filename] = cleaned
            self.sourcedid_cache[filename] = seen

        except Exception as e:
            self.errors.append(ValidationError(file=filename, line=0, field='', message=str(e)))

    def _validate_record(self, filename: str, record: Dict[str,str], line: int) -> bool:
        ok = True
        if not self._validate_required_fields(filename, record, line): ok = False
        if not self._validate_data_types(filename, record, line): ok = False
        if not self._validate_cross_reference(filename, record, line): ok = False
        return ok

    def _validate_required_fields(self, filename: str, record: Dict[str,str], line: int) -> bool:
        required = {
            'orgs.csv': ['sourcedId','name','type'],
            'users.csv': ['sourcedId','username'],
            'roles.csv': ['userSourcedId','orgSourcedId','role'],
            'classes.csv': ['sourcedId','orgSourcedId','title'],
            'enrollments.csv': ['classSourcedId','userSourcedId','role'],
            'academicSessions.csv': ['sourcedId','title','type','startDate','endDate'],
            'courses.csv': ['sourcedId','orgSourcedId','title']
        }
        # SDS V2.1互換の必須フィールド
        sds_v21_required = {
            'roles.csv': ['sourcedId', 'userSourcedId', 'orgSourcedId', 'role'],
            'enrollments.csv': ['sourcedId', 'classSourcedId', 'userSourcedId', 'role']
        }
        
        ok = True
        req_fields = required.get(filename, [])
        
        # SDS V2.1互換の場合は対応する必須フィールドを使用
        if filename in sds_v21_required and 'sourcedId' in record:
            req_fields = sds_v21_required[filename]
            
        for fld in req_fields:
            if not record.get(fld):
                self.errors.append(ValidationError(
                    file=filename, line=line, field=fld,
                    message=f'Required field {fld} missing'
                ))
                ok = False
        return ok

    def _validate_data_types(self, filename: str, record: Dict[str,str], line: int) -> bool:
        ok = True
        if 'email' in record and record['email'] and not self._is_valid_email(record['email']):
            self.errors.append(ValidationError(file=filename,line=line,field='email',message=f'Invalid email {record["email"]}'))
            ok = False
        if 'phone' in record and record['phone'] and not self._is_valid_phone(record['phone']):
            self.errors.append(ValidationError(file=filename,line=line,field='phone',message=f'Invalid phone {record["phone"]}'))
            ok = False
        for dt in ['startDate','endDate','roleStartDate','roleEndDate']:
            if dt in record and record[dt] and not self._is_valid_date(record[dt]):
                self.errors.append(ValidationError(file=filename,line=line,field=dt,message=f'Invalid date {record[dt]}'))
                ok = False
        if 'enabledUser' in record and record['enabledUser'] not in ['true','false']:
            self.errors.append(ValidationError(file=filename,line=line,field='enabledUser',message=f'Invalid boolean {record["enabledUser"]}'))
            ok = False
        return ok

    def _validate_cross_reference(self, filename: str, record: Dict[str,str], line: int) -> bool:
        ok = True
        if filename == 'roles.csv':
            if 'users.csv' in self.sourcedid_cache and record['userSourcedId'] not in self.sourcedid_cache['users.csv']:
                self.errors.append(ValidationError(file=filename,line=line,field='userSourcedId',message=f'Missing ref {record["userSourcedId"]}'))
                ok = False
            if 'orgs.csv' in self.sourcedid_cache and record['orgSourcedId'] not in self.sourcedid_cache['orgs.csv']:
                self.errors.append(ValidationError(file=filename,line=line,field='orgSourcedId',message=f'Missing ref {record["orgSourcedId"]}'))
                ok = False
        if filename == 'enrollments.csv':
            if 'users.csv' in self.sourcedid_cache and record['userSourcedId'] not in self.sourcedid_cache['users.csv']:
                self.errors.append(ValidationError(file=filename,line=line,field='userSourcedId',message=f'Missing ref {record["userSourcedId"]}'))
                ok = False
            if 'classes.csv' in self.sourcedid_cache and record['classSourcedId'] not in self.sourcedid_cache['classes.csv']:
                self.errors.append(ValidationError(file=filename,line=line,field='classSourcedId',message=f'Missing ref {record["classSourcedId"]}'))
                ok = False
        return ok

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        _, a = parseaddr(email)
        return bool(a and '@' in a and a == a.lower())

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        try:
            p = phonenumbers.parse(phone, None)
            return phonenumbers.is_valid_number(p)
        except:
            return False

    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False


def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python sds_validator.py <CSV directory>")
        sys.exit(1)
    validator = SDSValidator(sys.argv[1])
    errors, out_dir, report_path = validator.validate_all()
    if errors:
        print("Errors detected. See report at:", report_path)
    else:
        print("No errors. Report at:", report_path)
    print("Cleaned files in:", out_dir)
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
