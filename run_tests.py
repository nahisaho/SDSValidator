#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SDS CSV バリデーションシステム用テストランナー
このスクリプトは単体テストと統合テストを実行します
"""
import unittest
import sys
import os
import argparse
from colorama import init, Fore, Style

# カラー出力の初期化
init()

def run_unit_tests():
    """単体テストを実行"""
    print(f"{Fore.CYAN}単体テスト (Unit Tests) を実行中...{Style.RESET_ALL}")
    from test_sds_validator import TestSDSValidator
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSDSValidator)
    return unittest.TextTestRunner(verbosity=2).run(suite)

def run_integration_tests():
    """統合テストを実行"""
    print(f"{Fore.CYAN}統合テスト (Integration Tests) を実行中...{Style.RESET_ALL}")
    from integration_test import TestSDSIntegration
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSDSIntegration)
    return unittest.TextTestRunner(verbosity=2).run(suite)

def run_all_tests():
    """すべてのテストを実行"""
    unit_result = run_unit_tests()
    print("\n" + "-" * 70 + "\n")
    integration_result = run_integration_tests()
    
    # 結果の集計
    total_tests = unit_result.testsRun + integration_result.testsRun
    total_failures = len(unit_result.failures) + len(integration_result.failures)
    total_errors = len(unit_result.errors) + len(integration_result.errors)
    
    print("\n" + "=" * 70)
    print(f"{Fore.CYAN}テスト実行サマリー:{Style.RESET_ALL}")
    print(f"合計テスト数: {total_tests}")
    
    if total_failures == 0 and total_errors == 0:
        print(f"{Fore.GREEN}全テスト成功！{Style.RESET_ALL}")
        return 0
    else:
        print(f"{Fore.RED}失敗: {total_failures}, エラー: {total_errors}{Style.RESET_ALL}")
        return 1

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='SDS CSV バリデータのテスト実行ツール')
    parser.add_argument('--unit', action='store_true', help='単体テストのみ実行')
    parser.add_argument('--integration', action='store_true', help='統合テストのみ実行')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細な出力')
    
    args = parser.parse_args()
    
    # 詳細モードの設定
    if args.verbose:
        unittest.TestCase.maxDiff = None
    
    # 指定されたテストを実行
    if args.unit:
        result = run_unit_tests()
        return 0 if len(result.failures) == 0 and len(result.errors) == 0 else 1
    elif args.integration:
        result = run_integration_tests()
        return 0 if len(result.failures) == 0 and len(result.errors) == 0 else 1
    else:
        return run_all_tests()

if __name__ == '__main__':
    try:
        # 必要なパッケージのチェック
        import colorama
    except ImportError:
        print("必要なパッケージがインストールされていません。")
        print("pip install colorama を実行してください。")
        sys.exit(1)
    
    # テスト実行
    sys.exit(main())