import os
import random
from datetime import datetime, timedelta
import csv

class SDSDataGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成するIDを保持
        self.org_ids = []
        self.user_ids = []
        self.class_ids = []
        self.course_ids = []
        self.session_ids = []

    def generate_all(self, num_orgs=5, num_users=50, num_classes=10):
        """すべてのサンプルデータを生成"""
        self.generate_orgs(num_orgs)
        self.generate_users(num_users)
        self.generate_courses(num_classes)
        self.generate_academic_sessions()
        self.generate_classes(num_classes)
        self.generate_roles()
        self.generate_enrollments()

    def generate_orgs(self, count: int):
        """組織データの生成"""
        filename = os.path.join(self.output_dir, 'orgs.csv')
        headers = ['sourcedId', 'name', 'type', 'parentSourcedId']
        org_types = ['school', 'department', 'district']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            # 親組織を作成
            parent_id = f'org_{1}'
            self.org_ids.append(parent_id)
            writer.writerow({
                'sourcedId': parent_id,
                'name': f'Organization {1}',
                'type': 'district',
                'parentSourcedId': ''
            })
            
            # 子組織を作成
            for i in range(2, count + 1):
                org_id = f'org_{i}'
                self.org_ids.append(org_id)
                writer.writerow({
                    'sourcedId': org_id,
                    'name': f'Organization {i}',
                    'type': random.choice(org_types),
                    'parentSourcedId': parent_id if random.random() > 0.5 else ''
                })

    def generate_users(self, count: int):
        """ユーザーデータの生成"""
        filename = os.path.join(self.output_dir, 'users.csv')
        headers = ['sourcedId','username','givenName','familyName','password','activeDirectoryMatchId','email','phone','sms']
        
        given_names = ['Alex', 'Chris', 'Pat', 'Jordan', 'Taylor']
        family_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for i in range(1, count + 1):
                user_id = f'user_{i}'
                self.user_ids.append(user_id)
                given_name = random.choice(given_names)
                family_name = random.choice(family_names)
                username = f'{given_name.lower()}.{family_name.lower()}{i}'
                
                writer.writerow({
                    'sourcedId': user_id,
                    'username': username,
                    'givenName': given_name,
                    'familyName': family_name,
                    'password': f'Pass{i}word!',
                    'activeDirectoryMatchId': f'AD{i}',
                    'email': f'{username}@example.com',
                    'phone': f'+8190{random.randint(10000000, 99999999)}',
                    'sms': f'+8180{random.randint(10000000, 99999999)}'
                })

    def generate_courses(self, count: int):
        """コースデータの生成"""
        filename = os.path.join(self.output_dir, 'courses.csv')
        headers = ['sourcedId', 'orgSourcedId', 'title', 'courseCode', 'grades']
        subjects = ['数学', '国語', '理科', '社会', '英語']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for i in range(1, count + 1):
                course_id = f'course_{i}'
                self.course_ids.append(course_id)
                subject = random.choice(subjects)
                
                writer.writerow({
                    'sourcedId': course_id,
                    'orgSourcedId': random.choice(self.org_ids),
                    'title': f'{subject} {i}',
                    'courseCode': f'SUBJ{i}',
                    'grades': f'Grade {random.randint(1, 12)}'
                })

    def generate_academic_sessions(self):
        """学期データの生成"""
        filename = os.path.join(self.output_dir, 'academicSessions.csv')
        headers = ['sourcedId', 'title', 'type', 'startDate', 'endDate', 'parentSourcedId']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            # 年度を作成
            year_id = 'session_2024'
            self.session_ids.append(year_id)
            writer.writerow({
                'sourcedId': year_id,
                'title': '2024年度',
                'type': 'schoolYear',
                'startDate': '2024-04-01',
                'endDate': '2025-03-31',
                'parentSourcedId': ''
            })
            
            # 学期を作成
            terms = [
                ('1学期', '2024-04-01', '2024-07-31'),
                ('2学期', '2024-09-01', '2024-12-31'),
                ('3学期', '2025-01-01', '2025-03-31')
            ]
            
            for i, (title, start, end) in enumerate(terms, 1):
                session_id = f'session_2024_term{i}'
                self.session_ids.append(session_id)
                writer.writerow({
                    'sourcedId': session_id,
                    'title': title,
                    'type': 'term',
                    'startDate': start,
                    'endDate': end,
                    'parentSourcedId': year_id
                })

    def generate_classes(self, count: int):
        """クラスデータの生成"""
        filename = os.path.join(self.output_dir, 'classes.csv')
        headers = ['sourcedId','orgSourcedId','title','sessionSourcedIds','courseSourcedId']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for i in range(1, count + 1):
                class_id = f'class_{i}'
                self.class_ids.append(class_id)
                course_id = random.choice(self.course_ids)
                term_ids = random.sample(self.session_ids, random.randint(1, 3))
                
                writer.writerow({
                    'sourcedId': class_id,
                    'orgSourcedId': random.choice(self.org_ids),
                    'title': f'Class {i}',
                    'sessionSourcedIds': ','.join(term_ids),
                    'courseSourcedId': course_id
                })

    def generate_roles(self):
        """役割データの生成"""
        filename = os.path.join(self.output_dir, 'roles.csv')
        headers = ['sourcedId', 'userSourcedId', 'orgSourcedId', 'role', 'sessionSourcedId']
        roles = ['teacher', 'student', 'administrator']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for i, user_id in enumerate(self.user_ids, 1):
                writer.writerow({
                    'sourcedId': f'role_{i}',
                    'userSourcedId': user_id,
                    'orgSourcedId': random.choice(self.org_ids),
                    'role': random.choice(roles),
                    'sessionSourcedId': random.choice(self.session_ids)
                })

    def generate_enrollments(self):
        """登録データの生成"""
        filename = os.path.join(self.output_dir, 'enrollments.csv')
        headers = ['sourcedId', 'classSourcedId', 'userSourcedId', 'role']
        roles = ['teacher', 'student']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            enrollment_count = len(self.user_ids) * 2  # 各ユーザーが平均2つのクラスに登録
            for i in range(1, enrollment_count + 1):
                writer.writerow({
                    'sourcedId': f'enrollment_{i}',
                    'classSourcedId': random.choice(self.class_ids),
                    'userSourcedId': random.choice(self.user_ids),
                    'role': random.choice(roles)
                })

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate sample SDS CSV files')
    parser.add_argument('output_dir', help='Output directory for CSV files')
    parser.add_argument('--orgs', type=int, default=5, help='Number of organizations')
    parser.add_argument('--users', type=int, default=50, help='Number of users')
    parser.add_argument('--classes', type=int, default=10, help='Number of classes')
    
    args = parser.parse_args()
    
    generator = SDSDataGenerator(args.output_dir)
    generator.generate_all(args.orgs, args.users, args.classes)
    print(f'サンプルデータを {args.output_dir} に生成しました')

if __name__ == '__main__':
    main()