S CSV バリデーションツール

Microsoft School Data Sync (SDS) V2.1 CSV ファイル形式のバリデーションを行うPythonツールです。

## 機能

### 1. バリデーション機能
- **ファイル構成の検証**
  - 必須ファイル（`classes.csv`、`enrollments.csv`、`orgs.csv`、`roles.csv`、`users.csv`）の存在確認
  - ヘッダーの正確性検証
  - 重複ヘッダーの検出
  - sourcedId の重複チェック

- **データ型と形式の検証**
  - メールアドレス（RFC 5322準拠、小文字）
  - 電話番号（E.164形式）
  - 日付（ISO 8601形式：YYYY-MM-DD）
  - ブール値（`true`/`false`）

- **必須フィールドの検証**
  - 各ファイルの必須フィールドの存在確認
  - 空値チェック

- **クロスリファレンスの検証**
  - `roles.csv`の参照整合性（userSourcedId, orgSourcedId）
  - `enrollments.csv`の参照整合性（classSourcedId, userSourcedId）
  - `classes.csv`の参照整合性（orgSourcedId）
  - `academicSessions.csv`の参照整合性
  - `orgs.csv`の参照整合性（parentSourcedId）

### 2. 出力機能
- 検証済みの正常データを `validated_output` ディレクトリに出力
- 削除されたレコードを `removed_records.json` に保存
- バリデーション結果を `validation_report.json` に保存

## インストール

1. 必要なPythonパッケージのインストール：
```bash
pip install -r requirements.txt
```

2. リポジトリのクローン：
```bash
git clone <repository-url>
cd sds-validator
```

## 使用方法

### バリデーションの実行

```bash
python sds_validator.py <CSVファイルのディレクトリパス>
```

### サンプルデータの生成（テスト用）

```bash
python generate_sample_data.py <出力ディレクトリ> [--orgs 組織数] [--users ユーザー数] [--classes クラス数]
```

### テストの実行

テストランナーを使用する（推奨）：
```bash
# すべてのテストを実行
python run_tests.py

# 単体テストのみ実行
python run_tests.py --unit

# 統合テストのみ実行
python run_tests.py --integration

# 詳細な出力で実行
python run_tests.py --verbose
```

単体テストを個別に実行：
```bash
python -m unittest test_sds_validator.py
```

統合テストを個別に実行：
```bash
python integration_test.py
```

## 出力結果

### 1. バリデーション結果
- 検証エラーがある場合、詳細なエラーメッセージを表示
- ファイル名、行番号、フィールド名、エラー内容を含む
- 戻り値は `(errors, output_dir, report_file)` の形式
  - `errors`: ValidationErrorオブジェクトのリスト
  - `output_dir`: 検証済みファイルの出力ディレクトリ
  - `report_file`: バリデーションレポートファイルのパス

### 2. 修正済みファイル
- `validated_output` ディレクトリに出力
- 無効なレコードを除外した新しいCSVファイル
- 元のヘッダー順序とフォーマットを維持

### 3. 削除レコード
- `removed_records.json` に保存
- 各ファイルごとに削除されたレコードを管理
- 削除理由の追跡が可能

## ファイル構成

```
.
├── README.md                    # このファイル
├── sds_validator.py             # メインのバリデーションツール
├── generate_sample_data.py      # テストデータ生成ツール
├── test_sds_validator.py        # 単体テスト
├── integration_test.py          # 統合テスト
└── run_tests.py                 # テスト実行ツール
```

## バリデーションルール

### 必須ファイル
- `orgs.csv`
- `users.csv`
- `roles.csv`

### オプションファイル
- `classes.csv`
- `enrollments.csv`
- `academicSessions.csv`
- `courses.csv`

### 各ファイルの期待されるヘッダー

#### orgs.csv
```
sourcedId, name, type, parentSourcedId
```

#### users.csv
```
sourcedId, username, givenName, familyName, password, activeDirectoryMatchId, email, phone, sms
```

#### roles.csv
```
userSourcedId, orgSourcedId, role, sessionSourcedId, grade, isPrimary, roleStartDate, roleEndDate
```
またはSDS V2.1互換:
```
sourcedId, userSourcedId, orgSourcedId, role, sessionSourcedId
```

#### classes.csv
```
sourcedId, orgSourcedId, title, sessionSourcedIds, courseSourcedId
```

#### enrollments.csv
```
classSourcedId, userSourcedId, role
```
またはSDS V2.1互換:
```
sourcedId, classSourcedId, userSourcedId, role
```

#### academicSessions.csv
```
sourcedId, title, type, startDate, endDate
```

#### courses.csv
```
sourcedId, orgSourcedId, title
```

### 各ファイルの必須フィールド

#### orgs.csv
- sourcedId
- name
- type

#### users.csv
- sourcedId
- username
- givenName
- familyName
- email
- enabledUser

#### roles.csv
- sourcedId
- userSourcedId
- orgSourcedId
- role

#### classes.csv
- sourcedId
- title
- orgSourcedId

#### enrollments.csv
- sourcedId
- classSourcedId
- userSourcedId
- role

#### academicSessions.csv
- sourcedId
- title
- type
- startDate
- endDate

#### courses.csv
- sourcedId
- orgSourcedId
- title

## エラーメッセージとエラーオブジェクト

バリデーションエラーは `ValidationError` オブジェクトとして返されます。各オブジェクトには以下のプロパティがあります：

- `file`: エラーが発生したファイル名
- `line`: エラーが発生した行番号（ヘッダー行は1）
- `field`: エラーが関連するフィールド名
- `message`: エラーメッセージ

プログラムは以下のような場合に特定のエラーメッセージを出力します：

1. ファイル構成エラー
   ```
   必須ファイル {filename} が見つかりません
   ```

2. ヘッダーエラー
   ```
   Invalid header. Expected [...], got [...]
   ```

3. sourcedId重複エラー
   ```
   重複するsourcedId: {value}（ファイル: {filename}）
   ```

4. データ形式エラー
   ```
   不正なメールアドレス形式: {value}
   不正な電話番号形式: {value}
   不正な日付形式: {value}
   ```

5. 参照整合性エラー
   ```
   参照先が存在しません: {value}（参照元: {source_file}、参照先: {target_file}）
   ```

## 実装上の注意点

- 必須ファイルのチェックは、指定されたディレクトリ内の各ファイルの存在を確認します
- ヘッダーバリデーションは、各ファイルの最初の行が正しいヘッダー順序かどうかを検証します
- sourcedId重複チェックは、同一ファイル内での sourcedId 値の重複を検出します
- メールアドレスバリデーションは、RFC 5322準拠の形式かどうかを検証します
- クロスリファレンスバリデーションは、一方のファイルから他方のファイルへの参照が有効かどうかを検証します

## テスト実行時のヒント

テストを実行する際、エラーメッセージを検索するときは以下のような形式で行います：

```python
# エラーオブジェクトからメッセージを取得する場合
any('エラー文字列' in str(e) for e in errors)

# またはエラーオブジェクトがdictの場合
any('エラー文字列' in e.get('message', '') for e in errors)
```

## サンプルデータ生成時の注意点

`generate_sample_data.py`を使用する場合：
- 必ず`generate_orgs()`を最初に実行してください（他のデータが組織IDに依存するため）
- データ生成の順序：orgs → users → roles → classes → enrollments
- 各メソッドが適切なIDリストを生成したことを確認してください（例：`self.org_ids`、`self.user_ids`など）

## ライセンス

MIT LICENSE

## 作者

Hisao Nakata (nahisaho@microsoft.com)