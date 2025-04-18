import unittest
import os
import shutil
import tempfile
from sds_validator import SDSValidator, ValidationError

class TestSDSValidator(unittest.TestCase):
    def setUp(self):
        # テスト用の一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # テスト終了後に一時ディレクトリを削除
        shutil.rmtree(self.test_dir)
        
    def create_test_file(self, filename, content):
        """テストファイルを作成するヘルパーメソッド"""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def flatten_errors(self, errors):
        """エラーリストをフラット化するヘルパー"""
        flat = []
        for e in errors:
            if isinstance(e, list):
                flat.extend(self.flatten_errors(e))
            else:
                flat.append(e)
        return flat

    def test_required_files(self):
        """必須ファイルの存在確認テスト"""
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        # 必須ファイルが存在しない場合、3つのエラーが含まれているはず
        required_file_errors = [e for e in errors if 'Required file' in e.message]
        self.assertGreaterEqual(len(errors), 3)
        self.assertEqual(len(required_file_errors), 3)
        self.assertTrue(any('Required file orgs.csv' in e.message for e in errors))
        self.assertTrue(any('Required file users.csv' in e.message for e in errors))
        self.assertTrue(any('Required file roles.csv' in e.message for e in errors))

    def test_header_validation(self):
        """ヘッダーバリデーションのテスト"""
        # 不正なヘッダーを持つusers.csvを作成
        self.create_test_file('users.csv', 'invalid_header1,invalid_header2\nvalue1,value2')
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        # ヘッダーエラーが含まれているか確認
        header_errors = [e for e in errors if e.field == 'header']
        self.assertTrue(any('Invalid header' in e.message for e in header_errors))

    def test_duplicate_sourcedId(self):
        """sourcedIdの重複チェックテスト"""
        # 重複するsourcedIdを持つusers.csvを作成
        content = (
            'sourcedId,username,givenName,familyName,password,activeDirectoryMatchId,email,phone,sms\n'
            'user1,user1,John,Doe,,12345,john@example.com,,\n'
            'user1,user2,Jane,Doe,,67890,jane@example.com,,'  # 重複するsourcedId
        )
        self.create_test_file('users.csv', content)
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        # sourcedIdの重複エラーが含まれているか確認
        self.assertTrue(any('Duplicate sourcedId' in e.message for e in errors))

    def test_email_validation(self):
        """メールアドレスバリデーションのテスト"""
        # 不正なメールアドレスを含むusers.csvを作成
        content = (
            'sourcedId,username,givenName,familyName,password,activeDirectoryMatchId,email,phone,sms\n'
            'user1,user1,John,Doe,,12345,invalid-email,,'
        )
        self.create_test_file('users.csv', content)
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        # メールアドレスエラーが含まれているか確認
        self.assertTrue(any('Invalid email' in e.message for e in errors))

    def test_phone_validation(self):
        """電話番号バリデーションのテスト"""
        # 不正な電話番号を含むusers.csvを作成
        content = (
            'sourcedId,username,givenName,familyName,password,activeDirectoryMatchId,email,phone,sms\n'
            'user1,user1,John,Doe,,12345,john@example.com,invalid-phone,'
        )
        self.create_test_file('users.csv', content)
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        # 電話番号エラーが含まれているか確認
        self.assertTrue(any('Invalid phone' in e.message for e in errors))

    def test_date_validation(self):
        """日付形式バリデーションのテスト"""
        # 不正な日付形式を含むroles.csvを作成
        # まずorgs.csv, users.csvを作成（参照整合性のため）
        orgs_content = 'sourcedId,name,type,parentSourcedId\norg1,Organization 1,school,'
        self.create_test_file('orgs.csv', orgs_content)
        
        users_content = 'sourcedId,username,givenName,familyName,password,activeDirectoryMatchId,email,phone,sms\nuser1,user1,John,Doe,,12345,john@example.com,,'
        self.create_test_file('users.csv', users_content)
        
        # 不正な日付形式を持つroles.csvを作成
        roles_content = (
            'userSourcedId,orgSourcedId,role,sessionSourcedId,grade,isPrimary,roleStartDate,roleEndDate\n'
            'user1,org1,teacher,,,,2023/04/01,2024/03/31'  # 不正な日付形式
        )
        self.create_test_file('roles.csv', roles_content)
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        # 日付形式エラーが含まれているか確認
        self.assertTrue(any('Invalid date' in e.message for e in errors))

    def test_required_fields(self):
        """必須フィールドのバリデーションテスト"""
        # 必須フィールドが不足するusers.csvを作成
        content = 'sourcedId,username,givenName,familyName,password,activeDirectoryMatchId,email,phone,sms\nuser1,,John,Doe,,12345,john@example.com,,'  # usernameが空
        self.create_test_file('users.csv', content)
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        # 必須フィールドエラーが含まれているか確認
        self.assertTrue(any('Required field username missing' in e.message for e in errors))

    def test_cross_reference_validation(self):
        """クロスリファレンスバリデーションのテスト"""
        # users.csvを作成
        users_content = (
            'sourcedId,username,givenName,familyName,password,activeDirectoryMatchId,email,phone,sms\n'
            'user1,user1,John,Doe,,12345,john@example.com,,'
        )
        self.create_test_file('users.csv', users_content)

        # org.csvを作成
        orgs_content = (
            'sourcedId,name,type,parentSourcedId\n'
            'org1,Organization 1,school,'
        )
        self.create_test_file('orgs.csv', orgs_content)
        
        # 存在しないユーザーを参照するroles.csvを作成
        roles_content = (
            'userSourcedId,orgSourcedId,role,sessionSourcedId,grade,isPrimary,roleStartDate,roleEndDate\n'
            'non_existent_user,org1,teacher,,,,,,'  # 存在しないユーザー
        )
        self.create_test_file('roles.csv', roles_content)
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        # 参照エラーが含まれているか確認
        self.assertTrue(any('Missing ref' in e.message for e in errors))

    def test_output_directory(self):
        """出力ディレクトリのテスト"""
        # 基本的なファイルを作成
        orgs_content = 'sourcedId,name,type,parentSourcedId\norg1,Organization 1,school,'
        self.create_test_file('orgs.csv', orgs_content)
        
        users_content = 'sourcedId,username,givenName,familyName,password,activeDirectoryMatchId,email,phone,sms\nuser1,user1,John,Doe,,12345,john@example.com,,'
        self.create_test_file('users.csv', users_content)
        
        roles_content = 'userSourcedId,orgSourcedId,role,sessionSourcedId,grade,isPrimary,roleStartDate,roleEndDate\nuser1,org1,teacher,,,,,,'
        self.create_test_file('roles.csv', roles_content)
        
        validator = SDSValidator(self.test_dir)
        _, output_dir, _ = validator.validate_all()
        
        # 出力ディレクトリが作成されたことを確認
        self.assertTrue(os.path.exists(output_dir))
        
        # 出力ファイルが作成されたことを確認
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'orgs.csv')))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'users.csv')))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'roles.csv')))

    def test_json_report(self):
        """JSONレポート出力のテスト"""
        # 基本的なファイルを作成（1つはエラーを含む）
        orgs_content = 'sourcedId,name,type,parentSourcedId\norg1,Organization 1,school,'
        self.create_test_file('orgs.csv', orgs_content)
        
        users_content = 'sourcedId,username,givenName,familyName,password,activeDirectoryMatchId,email,phone,sms\nuser1,user1,John,Doe,,12345,invalid-email,,'  # 無効なメール
        self.create_test_file('users.csv', users_content)
        
        roles_content = 'userSourcedId,orgSourcedId,role,sessionSourcedId,grade,isPrimary,roleStartDate,roleEndDate\nuser1,org1,teacher,,,,,,'
        self.create_test_file('roles.csv', roles_content)
        
        validator = SDSValidator(self.test_dir)
        errors, _, report_path = validator.validate_all()
        
        # レポートファイルが作成されたことを確認
        self.assertTrue(os.path.exists(report_path))
        
        # レポートが読み込めてJSONとして妥当なことを確認
        try:
            import json
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                
            self.assertTrue(isinstance(report, dict))
            self.assertTrue('hasErrors' in report)
            self.assertTrue(report['hasErrors'])  # エラーが検知されているはず
            self.assertTrue('errors' in report)
            self.assertTrue(len(report['errors']) > 0)
        except Exception as e:
            self.fail(f"JSONレポートが無効です: {str(e)}")

if __name__ == '__main__':
    unittest.main()