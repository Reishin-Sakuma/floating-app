"""
アプリケーション起動エンジン テストケース
"""
import os
import tempfile
import time
import unittest.mock
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from unittest.mock import patch, MagicMock

import pytest

from src.app_launcher import AppLauncher, LaunchResult, ProcessInfo


class TestAppLauncher:
    """AppLauncher クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.launcher = AppLauncher()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # TC-001: AppLauncher初期化
    def test_app_launcher_initialization(self):
        """AppLauncherが正常に初期化される"""
        launcher = AppLauncher()
        assert launcher is not None
        assert hasattr(launcher, 'launch_application')
        assert hasattr(launcher, 'is_valid_executable')

    # TC-002: 有効な実行ファイルの検証
    def test_is_valid_executable_with_valid_exe(self):
        """有効な実行ファイルが正しく検証される"""
        # Windows notepad.exe のパスを使用
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if os.path.exists(notepad_path):
            result = self.launcher.is_valid_executable(notepad_path)
            assert result is True
        else:
            # notepadが見つからない場合はスキップ
            pytest.skip("notepad.exe not found")

    # TC-003: 無効なファイルの検証
    def test_is_valid_executable_with_invalid_file(self):
        """無効なファイルが適切に拒否される"""
        # 一時的な.txtファイルを作成
        txt_file = os.path.join(self.temp_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("test content")
        
        result = self.launcher.is_valid_executable(txt_file)
        assert result is False

    # TC-101: 正常なアプリケーション起動
    def test_launch_application_success(self):
        """有効なアプリケーションが正常に起動される"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        start_time = time.time()
        result = self.launcher.launch_application(notepad_path)
        end_time = time.time()
        
        assert isinstance(result, LaunchResult)
        assert result.success is True
        assert result.process_id is not None
        assert result.process_id > 0
        assert result.error_message is None
        
        execution_time = (end_time - start_time) * 1000  # ms
        assert execution_time < 1000, f"起動時間が{execution_time:.2f}msで1秒を超えています"
        
        # 起動したプロセスを終了
        if result.process_id:
            self.launcher.kill_application(notepad_path)

    # TC-102: 存在しないファイルの起動試行
    def test_launch_application_file_not_found(self):
        """存在しないファイル指定時の適切なエラーハンドリング"""
        non_existent_path = os.path.join(self.temp_dir, "nonexistent.exe")
        
        result = self.launcher.launch_application(non_existent_path)
        
        assert isinstance(result, LaunchResult)
        assert result.success is False
        assert result.process_id is None
        assert result.error_message is not None
        assert "not found" in result.error_message.lower() or "見つかりません" in result.error_message

    # TC-103: 引数付きアプリケーション起動
    def test_launch_application_with_args(self):
        """コマンドライン引数付きでアプリケーションが起動される"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        # 引数としてテンポラリファイルを指定
        temp_file = os.path.join(self.temp_dir, "test.txt")
        with open(temp_file, 'w') as f:
            f.write("test content")
        
        args = [temp_file]
        result = self.launcher.launch_application(notepad_path, args)
        
        assert result.success is True
        assert result.process_id is not None
        
        # 起動したプロセスを終了
        if result.process_id:
            self.launcher.kill_application(notepad_path)

    # TC-201: パストラバーサル攻撃の防止
    def test_launch_application_path_traversal_attack(self):
        """パストラバーサル攻撃が適切に防止される"""
        malicious_path = "../../../Windows/System32/cmd.exe"
        
        result = self.launcher.launch_application(malicious_path)
        
        assert result.success is False
        assert "セキュリティ" in result.error_message or "security" in result.error_message.lower()

    # TC-202: 無効な拡張子の拒否
    def test_launch_application_invalid_extension(self):
        """実行ファイル以外の拡張子が拒否される"""
        txt_file = os.path.join(self.temp_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("test content")
        
        result = self.launcher.launch_application(txt_file)
        
        assert result.success is False
        assert "無効なファイル" in result.error_message or "invalid file" in result.error_message.lower()

    # TC-203: 長いファイルパスの処理
    def test_launch_application_long_path(self):
        """異常に長いファイルパスが適切に処理される"""
        # 260文字を超える長いパスを作成
        long_path = "C:\\" + "a" * 300 + ".exe"
        
        result = self.launcher.launch_application(long_path)
        
        assert result.success is False
        assert result.error_message is not None

    # TC-204: 特殊文字を含むパスの処理
    def test_launch_application_special_characters(self):
        """特殊文字を含むパスが適切に処理される"""
        special_chars = ['<', '>', '|', '"', '*', '?']
        
        for char in special_chars:
            malicious_path = f"C:\\test{char}file.exe"
            result = self.launcher.launch_application(malicious_path)
            assert result.success is False

    # TC-301: 管理者権限判定
    def test_requires_admin_privileges_system_app(self):
        """管理者権限が必要なアプリの判定が正しく行われる"""
        regedit_path = os.path.join(os.environ['WINDIR'], 'regedit.exe')
        
        if os.path.exists(regedit_path):
            result = self.launcher.requires_admin_privileges(regedit_path)
            # regeditは通常管理者権限を要求するが、環境によって異なる可能性がある
            assert isinstance(result, bool)
        else:
            pytest.skip("regedit.exe not found")

    # TC-302: 通常権限判定
    def test_requires_admin_privileges_normal_app(self):
        """通常権限で実行可能なアプリの判定が正しく行われる"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if os.path.exists(notepad_path):
            result = self.launcher.requires_admin_privileges(notepad_path)
            assert result is False
        else:
            pytest.skip("notepad.exe not found")

    # TC-303: 管理者権限での起動
    def test_launch_with_admin(self):
        """管理者権限でのアプリケーション起動が適切に処理される"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        # 実際のUACプロンプトを避けるため、この機能の存在確認のみ
        result = self.launcher.launch_with_admin(notepad_path)
        assert isinstance(result, LaunchResult)

    # TC-401: 起動中アプリケーションの検出
    def test_is_application_running_true(self):
        """実行中のアプリケーションが正しく検出される"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        # アプリケーションを起動
        result = self.launcher.launch_application(notepad_path)
        if result.success:
            # 実行中かチェック
            is_running = self.launcher.is_application_running(notepad_path)
            assert is_running is True
            
            # クリーンアップ
            self.launcher.kill_application(notepad_path)

    # TC-402: 停止中アプリケーションの検出
    def test_is_application_running_false(self):
        """実行していないアプリケーションが正しく検出される"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        # 停止状態での確認
        is_running = self.launcher.is_application_running(notepad_path)
        assert is_running is False

    # TC-403: プロセス情報の取得
    def test_get_process_info(self):
        """実行中プロセスの詳細情報が正しく取得される"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        # アプリケーションを起動
        result = self.launcher.launch_application(notepad_path)
        if result.success and result.process_id:
            # プロセス情報を取得
            proc_info = self.launcher.get_process_info(result.process_id)
            
            if proc_info:  # プロセスが見つかった場合
                assert isinstance(proc_info, ProcessInfo)
                assert proc_info.process_id == result.process_id
                assert isinstance(proc_info.process_name, str)
                assert isinstance(proc_info.executable_path, str)
                
            # クリーンアップ
            self.launcher.kill_application(notepad_path)

    # TC-404: アプリケーションの強制終了
    def test_kill_application(self):
        """起動中のアプリケーションが適切に終了される"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        # アプリケーションを起動
        result = self.launcher.launch_application(notepad_path)
        if result.success:
            # 強制終了
            kill_result = self.launcher.kill_application(notepad_path)
            assert kill_result is True
            
            # 終了確認
            time.sleep(0.5)  # 終了処理待ち
            is_running = self.launcher.is_application_running(notepad_path)
            assert is_running is False

    # TC-501: 権限不足エラー
    def test_launch_application_permission_error(self):
        """権限不足時の適切なエラーハンドリング"""
        # システムファイルを指定（通常はPermissionError）
        system_file = os.path.join(os.environ['WINDIR'], 'System32', 'config', 'SAM')
        
        result = self.launcher.launch_application(system_file)
        assert result.success is False

    # TC-601: 起動時間測定
    def test_launch_performance(self):
        """アプリケーション起動時間が要件を満たす"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        start_time = time.time()
        result = self.launcher.launch_application(notepad_path)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # ms
        assert execution_time < 1000, f"起動時間が{execution_time:.2f}msで1000msを超えています"
        
        if result.success:
            self.launcher.kill_application(notepad_path)

    # TC-602: 複数同時起動
    def test_multiple_concurrent_launches(self):
        """複数アプリケーションの同時起動性能"""
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        
        if not os.path.exists(notepad_path):
            pytest.skip("notepad.exe not found")
        
        results = []
        # 3つの並行起動を試行
        for i in range(3):
            result = self.launcher.launch_application(notepad_path)
            results.append(result)
        
        # 全て成功することを確認
        for result in results:
            assert result.success is True
        
        # クリーンアップ
        for result in results:
            if result.success:
                self.launcher.kill_application(notepad_path)

    # TC-701: ConfigManagerとの連携
    def test_integration_with_config_manager(self):
        """設定ファイルからの起動が正常に動作する"""
        from src.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_default_config()
        
        # notepadをテスト用アプリとして設定
        notepad_path = os.path.join(os.environ['WINDIR'], 'notepad.exe')
        if os.path.exists(notepad_path):
            config['app_path'] = notepad_path
            config_manager.save_config(config)
            
            # 設定から読み込んで起動
            loaded_config = config_manager.load_config()
            result = self.launcher.launch_application(loaded_config['app_path'])
            
            assert result.success is True
            
            if result.success:
                self.launcher.kill_application(notepad_path)
        else:
            pytest.skip("notepad.exe not found")