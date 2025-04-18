import unittest
import os
import shutil
import tempfile
import json
from datetime import datetime, timedelta
from generate_sample_data import SDSDataGenerator
from sds_validator import SDSValidator

class TestSDSIntegration(unittest.TestCase):
    def setUp(self):
        """テスト環境のセットアップ"""
        self.test_dir = tempfile.mkdtemp()
        self.generator = SDSDataGenerator(self.test_dir)
        
    def tearDown(self):
        """テスト環境のクリーンアップ"""
        shutil.rmtree(self.test_dir)
        
    def test_valid_data(self):
        """正常なデータセットのテスト"""
        # 標準的なデータセットを生成
        self.generator.generate_all(num_orgs=3, num_users=10, num_classes=5)
        
        # バリデーション実行
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        
        # エラーがないことを確認
        self.assertEqual(len(errors), 0, f"エラーが発生: {errors}")

    def test_invalid_email(self):
        """不正なメールアドレスのテスト"""
        self.generator.generate_all(num_orgs=2, num_users=5, num_classes=2)
        
        # users.csvを読み込んで不正なメールアドレスに書き換え
        users_file = os.path.join(self.test_dir, 'users.csv')
        with open(users_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 2行目（最初のデータ行）のメールアドレスを不正な形式に変更
        parts = lines[1].split(',')
        email_index = 6  # CSVのメールアドレス位置
        parts[email_index] = 'invalid.email'  # メールアドレスフィールドを書き換え
        lines[1] = ','.join(parts)
        
        with open(users_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        
        # メールアドレスに関するエラーが含まれていることを確認
        self.assertTrue(any('Invalid email' in e.message for e in errors))

    def test_invalid_cross_reference(self):
        """不正な参照関係のテスト"""
        self.generator.generate_all(num_orgs=2, num_users=5, num_classes=2)
        
        # roles.csvに存在しないユーザーIDへの参照を追加
        roles_file = os.path.join(self.test_dir, 'roles.csv')
        with open(roles_file, 'a', encoding='utf-8') as f:
            f.write(f'non_existent_user,{self.generator.org_ids[0]},teacher,,,,,\n')
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        
        # 参照エラーが含まれていることを確認
        self.assertTrue(any('Missing ref' in e.message for e in errors))

    def test_duplicate_sourcedId(self):
        """重複するsourcedIdのテスト"""
        self.generator.generate_all(num_orgs=2, num_users=5, num_classes=2)
        
        # users.csvに重複するsourcedIdを追加
        users_file = os.path.join(self.test_dir, 'users.csv')
        duplicate_user = self.generator.user_ids[0]  # 既存のユーザーIDを使用
        
        # 既存のCSVの構造を確認
        with open(users_file, 'r', encoding='utf-8') as f:
            header = f.readline().strip()
            field_count = len(header.split(','))
        
        with open(users_file, 'a', encoding='utf-8') as f:
            duplicate_entry = [duplicate_user, 'duplicate.user', 'John', 'Doe', '', '12345', 'john.doe@example.com', '', '']
            # 必要に応じてフィールド数を調整
            while len(duplicate_entry) < field_count:
                duplicate_entry.append('')
            f.write(','.join(duplicate_entry) + '\n')
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        
        # 重複エラーが含まれていることを確認
        self.assertTrue(any('Duplicate sourcedId' in e.message for e in errors))

    def test_missing_required_file(self):
        """必須ファイルの欠落テスト"""
        # users.csvのみを生成
        self.generator.generate_users(5)
        
        validator = SDSValidator(self.test_dir)
        errors, _, _ = validator.validate_all()
        
        # roles.csvとorgs.csvが欠落しているというエラーが含まれていることを確認
        self.assertTrue(any('Required file orgs.csv' in e.message for e in errors))
        self.assertTrue(any('Required file roles.csv' in e.message for e in errors))

    def test_invalid_date_format(self):
        """不正な日付形式のテスト"""
        self.generator.generate_all(num_orgs=2, num_users=5, num_classes=2)
        
        # roles.csvの日付形式を不正に変更
        roles_file = os.path.join(self.test_dir, 'roles.csv')
        with open(roles_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            header = lines[0].strip().split(',')
            
        # roleStartDateとroleEndDateのインデックスを見つける
        start_date_idx = header.index('roleStartDate') if 'roleStartDate' in header else -1
        end_date_idx = header.index('roleEndDate') if 'roleEndDate' in header else -1
        
        if start_date_idx >= 0 and len(lines) > 1:
            # 2行目の開始日を不正な形式に変更
            parts = lines[1].split(',')
            if len(parts) > start_date_idx:
                parts[start_date_idx] = '2023/04/01'  # 不正な日付形式
                lines[1] = ','.join(parts)
                
                with open(roles_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                validator = SDSValidator(self.test_dir)
                errors, _, _ = validator.validate_all()
                
                # 日付形式エラーが含まれていることを確認
                self.assertTrue(any('Invalid date' in e.message for e in errors))

    def test_full_flow(self):
        """エンドツーエンドのフル検証フロー"""
        # 1. 妥当なデータを生成
        self.generator.generate_all(num_orgs=5, num_users=20, num_classes=10)
        
        # 2. いくつかの問題を意図的に導入
        # 2.1 無効なメールアドレス
        users_file = os.path.join(self.test_dir, 'users.csv')
        self._modify_csv_field(users_file, 1, 'email', 'invalid-email')
        
        # 2.2 重複するID
        orgs_file = os.path.join(self.test_dir, 'orgs.csv')
        with open(orgs_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            first_org_id = lines[1].split(',')[0]
        
        with open(orgs_file, 'a', encoding='utf-8') as f:
            f.write(f"{first_org_id},Duplicate Org,school,\n")
        
        # 3. バリデーション実行
        validator = SDSValidator(self.test_dir)
        errors, output_dir, report_path = validator.validate_all()
        
        # 4. 結果検証
        # 4.1 エラーが検出されたことを確認
        self.assertTrue(len(errors) >= 2)  # 少なくとも2つのエラー
        
        # 4.2 出力ディレクトリが作成されたことを確認
        self.assertTrue(os.path.exists(output_dir))
        
        # 4.3 レポートファイルが作成されたことを確認
        self.assertTrue(os.path.exists(report_path))
        
        # 4.4 レポート内容を検証
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                self.assertTrue(report['hasErrors'])
                self.assertTrue(len(report['errors']) >= 2)
        except Exception as e:
            self.fail(f"JSONレポートが無効です: {str(e)}")
            
    def _modify_csv_field(self, file_path, row_num, field_name, new_value):
        """CSVファイルの特定フィールドを変更するヘルパーメソッド"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            header = lines[0].strip().split(',')
            
        if field_name in header and row_num < len(lines):
            field_idx = header.index(field_name)
            parts = lines[row_num].split(',')
            if field_idx < len(parts):
                parts[field_idx] = new_value
                lines[row_num] = ','.join(parts)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True
        return False

def main():
    # テストスイートのセットアップ
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSDSIntegration)
    
    # テスト結果を詳細に表示するためのランナーを使用
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    main()