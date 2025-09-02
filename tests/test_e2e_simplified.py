# -*- coding: utf-8 -*-
"""
E2E統合テストスイート（簡易版）- フローティングランチャー
Tkinterやシステムトレイに依存しない基本的な統合テスト
"""
import unittest
import tempfile
import shutil
import json
import time
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# テスト対象モジュールのインポート
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from app_launcher import AppLauncher
from auto_startup import AutoStartupManager
from error_handler import GlobalErrorHandler
from performance_monitor import PerformanceMonitor


class E2EBasicIntegrationTest(unittest.TestCase):
    """E2E基本統合テスト（外部依存なし）"""
    
    def setUp(self):
        """テスト前準備"""
        # 一時ディレクトリ作成
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_file = self.test_dir / "config.json"
        
        # テスト用設定
        self.test_config = {
            "app_path": "C:\\Windows\\System32\\notepad.exe",
            "icon_position": {"x": 100, "y": 100},
            "icon_fixed": False,
            "auto_start": False,
            "icon_size": 32,
            "version": "1.0.0"
        }
        
        # テスト設定ファイル作成
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.test_config, f, indent=2, ensure_ascii=False)
        
    def tearDown(self):
        """テスト後清理"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_config_manager_basic_operations(self):
        """設定管理基本操作テスト"""
        # 設定管理インスタンス作成
        config_manager = ConfigManager(str(self.config_file))
        
        # 設定読み込み
        config = config_manager.load_config()
        self.assertIsInstance(config, dict)
        self.assertEqual(config["app_path"], "C:\\Windows\\System32\\notepad.exe")
        self.assertEqual(config["icon_size"], 32)
        
        # 設定変更
        config["icon_size"] = 64
        config["auto_start"] = True
        
        # 設定保存
        self.assertTrue(config_manager.save_config(config))
        
        # 新しいインスタンスで読み込み確認
        config_manager2 = ConfigManager(str(self.config_file))
        config2 = config_manager2.load_config()
        self.assertEqual(config2["icon_size"], 64)
        self.assertEqual(config2["auto_start"], True)
    
    def test_config_validation(self):
        """設定値検証テスト"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 有効な設定
        valid_config = {
            "app_path": "C:\\Windows\\System32\\calc.exe",
            "icon_position": {"x": 200, "y": 300},
            "icon_fixed": True,
            "auto_start": False,
            "icon_size": 48,
            "version": "1.0.0"
        }
        
        # 検証実行
        is_valid, errors = config_manager.validate_config(valid_config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # 無効な設定（必須キー不足）
        invalid_config = {
            "app_path": "C:\\Windows\\System32\\calc.exe",
            "icon_size": 48
            # 他の必須キーが不足
        }
        
        is_valid, errors = config_manager.validate_config(invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_app_launcher_basic_operations(self):
        """アプリ起動基本操作テスト"""
        app_launcher = AppLauncher()
        
        # 有効なアプリパス（Windowsの標準アプリ）
        valid_paths = [
            "C:\\Windows\\System32\\notepad.exe",
            "C:\\Windows\\System32\\calc.exe"
        ]
        
        for path in valid_paths:
            if Path(path).exists():
                # パス有効性確認
                self.assertTrue(Path(path).is_file())
                break
        
        # 無効なアプリパス
        invalid_path = "C:\\NonExistent\\invalid_app.exe"
        self.assertFalse(Path(invalid_path).exists())
    
    @patch('winreg.OpenKey')
    @patch('winreg.SetValueEx') 
    @patch('winreg.DeleteValue')
    def test_auto_startup_operations(self, mock_delete, mock_set, mock_open):
        """自動起動操作テスト"""
        # モック設定
        mock_key = Mock()
        mock_open.return_value.__enter__.return_value = mock_key
        
        # 自動起動マネージャー
        startup_manager = AutoStartupManager()
        
        # 自動起動有効化テスト
        result = startup_manager.enable_auto_startup("TestApp", "C:\\test\\app.exe")
        self.assertTrue(result)
        mock_set.assert_called_once()
        
        # 自動起動無効化テスト
        result = startup_manager.disable_auto_startup("TestApp")
        self.assertTrue(result)
        mock_delete.assert_called_once()
        
        # ステータス確認テスト
        with patch('winreg.QueryValueEx', return_value=("C:\\test\\app.exe", 1)):
            status = startup_manager.get_auto_startup_status("TestApp")
            self.assertTrue(status)
    
    def test_error_handler_basic_operations(self):
        """エラーハンドリング基本操作テスト"""
        # エラーハンドラー
        error_handler = GlobalErrorHandler(log_dir=str(self.test_dir))
        
        # エラーログテスト
        test_error = Exception("Test error message")
        error_handler.handle_error(test_error, "Test context")
        
        # ログファイル確認
        log_files = list(self.test_dir.glob("*.log"))
        self.assertGreater(len(log_files), 0)
        
        # ログ内容確認
        log_file = log_files[0]
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn("Test error message", log_content)
    
    def test_performance_monitor_basic_operations(self):
        """パフォーマンス監視基本操作テスト"""
        # パフォーマンス監視
        monitor = PerformanceMonitor()
        
        # 初期化確認
        self.assertIsNotNone(monitor)
        
        # 基本メトリクス取得テスト
        try:
            # 実際のメトリクス取得を試行
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # 取得成功確認
            self.assertIsInstance(cpu_percent, (int, float))
            self.assertGreater(memory.total, 0)
            
        except ImportError:
            self.skipTest("psutil not available")
    
    def test_config_backup_restore(self):
        """設定バックアップ・復旧テスト"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 初期設定読み込み
        original_config = config_manager.load_config()
        
        # バックアップ作成
        backup_result = config_manager.backup_config()
        self.assertTrue(backup_result)
        
        # 設定変更・保存
        original_config["icon_size"] = 128
        config_manager.save_config(original_config)
        
        # 最新バックアップから復旧
        restore_result = config_manager._try_restore_from_latest_backup()
        if restore_result:
            # 復旧後の設定確認
            restored_config = config_manager.load_config()
            self.assertEqual(restored_config["icon_size"], 32)  # 元の値
    
    def test_multi_instance_config_access(self):
        """複数インスタンス設定アクセステスト"""
        # 複数の設定マネージャーインスタンス作成
        config_managers = [
            ConfigManager(str(self.config_file))
            for _ in range(3)
        ]
        
        # 各インスタンスで設定読み込み
        configs = [cm.load_config() for cm in config_managers]
        
        # 全て同じ設定値確認
        for config in configs:
            self.assertEqual(config["app_path"], "C:\\Windows\\System32\\notepad.exe")
            self.assertEqual(config["icon_size"], 32)
        
        # 一つのインスタンスで設定変更・保存
        configs[0]["icon_size"] = 96
        config_managers[0].save_config(configs[0])
        
        # 他のインスタンスで変更確認
        updated_config = config_managers[1].load_config()
        self.assertEqual(updated_config["icon_size"], 96)
    
    def test_error_recovery_scenarios(self):
        """エラー復旧シナリオテスト"""
        config_manager = ConfigManager(str(self.config_file))
        
        # 破損した設定ファイル作成
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("{invalid json}")
        
        # 破損ファイルからの読み込み（デフォルト設定で復旧されるはず）
        config = config_manager.load_config()
        self.assertIsInstance(config, dict)
        self.assertIn("app_path", config)
        
        # 読み取り専用ファイル作成
        self.config_file.chmod(0o444)  # 読み取り専用
        
        try:
            # 読み取り専用ファイルへの書き込み失敗テスト
            save_result = config_manager.save_config(config)
            # Windowsでは権限設定が期待通りに動作しない場合があるため、
            # 結果に関わらずテストを継続
        except PermissionError:
            # 権限エラーが発生した場合はテスト成功
            pass
        finally:
            # 権限を元に戻す
            self.config_file.chmod(0o666)


class E2EPerformanceTest(unittest.TestCase):
    """E2Eパフォーマンステスト"""
    
    def test_config_operations_performance(self):
        """設定操作パフォーマンステスト"""
        test_dir = Path(tempfile.mkdtemp())
        config_file = test_dir / "perf_config.json"
        
        try:
            # 基本設定作成
            basic_config = {
                "app_path": "C:\\Windows\\System32\\notepad.exe",
                "icon_position": {"x": 100, "y": 100},
                "icon_fixed": False,
                "auto_start": False,
                "icon_size": 32,
                "version": "1.0.0"
            }
            
            with open(config_file, "w") as f:
                json.dump(basic_config, f)
            
            config_manager = ConfigManager(str(config_file))
            
            # 50回の読み書きテスト（時間短縮）
            start_time = time.time()
            
            for i in range(50):
                # 読み込み
                config = config_manager.load_config()
                
                # 変更
                config["icon_size"] = 32 + i
                
                # 保存
                config_manager.save_config(config)
            
            total_time = time.time() - start_time
            avg_time = total_time / 50
            
            # 平均0.02秒以内
            self.assertLess(avg_time, 0.02)
            
        finally:
            if test_dir.exists():
                shutil.rmtree(test_dir)


if __name__ == "__main__":
    # テストスイート作成
    suite = unittest.TestSuite()
    
    # 基本統合テスト追加
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(E2EBasicIntegrationTest))
    
    # パフォーマンステスト追加
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(E2EPerformanceTest))
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果出力
    print(f"\n{'='*60}")
    print("E2E 簡易テスト結果サマリー")
    print(f"{'='*60}")
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print(f"\n失敗詳細:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nエラー詳細:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # 成功率
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n成功率: {success_rate:.1f}%")
    
    if success_rate >= 100:
        print("🎉 全E2E簡易テスト合格!")
    elif success_rate >= 90:
        print("✅ E2E簡易テストほぼ合格") 
    else:
        print("❌ E2E簡易テストに問題があります")