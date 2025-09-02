"""
設定ファイル管理システム テストケース
"""
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from src.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.manager = ConfigManager(self.config_file)

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # TC-001: ConfigManager初期化
    def test_config_manager_initialization(self):
        """ConfigManagerが正常に初期化される"""
        manager = ConfigManager()
        assert manager is not None
        assert hasattr(manager, 'config_file_path')
        
        # カスタムパス指定の初期化
        custom_manager = ConfigManager(self.config_file)
        assert custom_manager.config_file_path == self.config_file

    # TC-002: デフォルト設定取得
    def test_get_default_config(self):
        """デフォルト設定が正しく返される"""
        default_config = self.manager.get_default_config()
        
        assert isinstance(default_config, dict)
        assert "app_path" in default_config
        assert "icon_position" in default_config
        assert "icon_fixed" in default_config
        assert "auto_start" in default_config
        assert "icon_size" in default_config
        assert "version" in default_config
        
        # 型チェック
        assert isinstance(default_config["app_path"], str)
        assert isinstance(default_config["icon_position"], dict)
        assert isinstance(default_config["icon_fixed"], bool)
        assert isinstance(default_config["auto_start"], bool)
        assert isinstance(default_config["icon_size"], int)
        assert isinstance(default_config["version"], str)
        
        # 位置情報の構造チェック
        assert "x" in default_config["icon_position"]
        assert "y" in default_config["icon_position"]

    # TC-101: 正常な設定ファイル読み込み
    def test_load_valid_config_file(self):
        """有効な設定ファイルが正しく読み込まれる"""
        expected_config = {
            "app_path": "C:\\Test\\app.exe",
            "icon_position": {"x": 200, "y": 300},
            "icon_fixed": True,
            "auto_start": False,
            "icon_size": 48,
            "version": "1.0.0"
        }
        
        # テスト用設定ファイル作成
        with open(self.config_file, 'w') as f:
            json.dump(expected_config, f)
        
        loaded_config = self.manager.load_config()
        assert loaded_config == expected_config

    # TC-102: 設定ファイルが存在しない場合
    def test_load_config_file_not_exists(self):
        """ファイルが存在しない場合にデフォルト設定が返される"""
        # 存在しないファイルパス
        non_existent_file = os.path.join(self.temp_dir, "non_existent.json")
        manager = ConfigManager(non_existent_file)
        
        config = manager.load_config()
        default_config = manager.get_default_config()
        
        assert config == default_config
        # 新しいファイルが作成されることを確認
        assert os.path.exists(non_existent_file)

    # TC-103: 破損した設定ファイル読み込み
    def test_load_corrupted_config_file(self):
        """JSONパースエラー時の自動復旧"""
        # 無効なJSONファイルを作成
        with open(self.config_file, 'w') as f:
            f.write("{ invalid json content }")
        
        config = self.manager.load_config()
        default_config = self.manager.get_default_config()
        
        # デフォルト設定が返されることを確認
        assert config == default_config

    # TC-201: 正常な設定保存
    def test_save_valid_config(self):
        """有効な設定が正しく保存される"""
        test_config = {
            "app_path": "C:\\Test\\save_test.exe",
            "icon_position": {"x": 150, "y": 250},
            "icon_fixed": False,
            "auto_start": True,
            "icon_size": 64,
            "version": "1.0.0"
        }
        
        result = self.manager.save_config(test_config)
        assert result is True
        assert os.path.exists(self.config_file)
        
        # 保存内容の確認（メタデータを除去）
        with open(self.config_file, 'r') as f:
            saved_data = json.load(f)
        saved_data_without_metadata = {k: v for k, v in saved_data.items() if k != '_metadata'}
        assert saved_data_without_metadata == test_config

    # TC-202: 書き込み権限エラー
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_save_config_permission_error(self, mock_file):
        """書き込み権限がない場合のエラーハンドリング"""
        test_config = {"app_path": "test.exe"}
        
        result = self.manager.save_config(test_config)
        assert result is False

    # TC-301: 有効な設定値のバリデーション
    def test_validate_valid_config(self):
        """正しい設定値がバリデーションをパスする"""
        valid_config = {
            "app_path": "",  # 空文字は許可
            "icon_position": {"x": 100, "y": 200},
            "icon_fixed": True,
            "auto_start": False,
            "icon_size": 32,
            "version": "1.0.0"
        }
        
        is_valid, errors = self.manager.validate_config(valid_config)
        assert is_valid is True
        assert errors == []

    # TC-302: 無効なapp_pathのバリデーション
    def test_validate_invalid_app_path(self):
        """無効なアプリケーションパスが検知される"""
        invalid_config = {
            "app_path": 12345,  # 文字列ではない値
            "icon_position": {"x": 100, "y": 200},
            "icon_fixed": True,
            "auto_start": False,
            "icon_size": 32,
            "version": "1.0.0"
        }
        
        is_valid, errors = self.manager.validate_config(invalid_config)
        assert is_valid is False
        assert len(errors) > 0
        assert any("app_path" in error for error in errors)

    # TC-303: 無効なicon_positionのバリデーション
    def test_validate_invalid_icon_position(self):
        """範囲外のアイコン位置が検知される"""
        invalid_config = {
            "app_path": "",
            "icon_position": {"x": 50000, "y": 200},  # 範囲外
            "icon_fixed": True,
            "auto_start": False,
            "icon_size": 32,
            "version": "1.0.0"
        }
        
        is_valid, errors = self.manager.validate_config(invalid_config)
        assert is_valid is False
        assert len(errors) > 0
        assert any("icon_position" in error for error in errors)

    # TC-304: 無効なicon_sizeのバリデーション
    def test_validate_invalid_icon_size(self):
        """範囲外のアイコンサイズが検知される"""
        invalid_config = {
            "app_path": "",
            "icon_position": {"x": 100, "y": 200},
            "icon_fixed": True,
            "auto_start": False,
            "icon_size": 200,  # 範囲外（16-128）
            "version": "1.0.0"
        }
        
        is_valid, errors = self.manager.validate_config(invalid_config)
        assert is_valid is False
        assert len(errors) > 0
        assert any("icon_size" in error for error in errors)

    # TC-401: 設定バックアップ作成
    def test_backup_config(self):
        """設定ファイルのバックアップが正しく作成される"""
        # 元の設定ファイル作成
        original_config = {"app_path": "test.exe", "version": "1.0.0"}
        with open(self.config_file, 'w') as f:
            json.dump(original_config, f)
        
        backup_path = self.manager.backup_config()
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        
        # バックアップ内容確認
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        assert backup_data == original_config

    # TC-402: バックアップからの復旧
    def test_restore_from_backup(self):
        """バックアップから設定が正しく復旧される"""
        backup_config = {"app_path": "backup_test.exe", "version": "1.0.0"}
        backup_file = os.path.join(self.temp_dir, "backup.json")
        
        # バックアップファイル作成
        with open(backup_file, 'w') as f:
            json.dump(backup_config, f)
        
        result = self.manager.restore_from_backup(backup_file)
        assert result is True
        
        # 復旧確認
        restored_config = self.manager.load_config()
        assert restored_config == backup_config

    # TC-403: 存在しないバックアップからの復旧
    def test_restore_from_non_existent_backup(self):
        """存在しないバックアップファイル指定時のエラーハンドリング"""
        non_existent_backup = os.path.join(self.temp_dir, "non_existent_backup.json")
        
        result = self.manager.restore_from_backup(non_existent_backup)
        assert result is False

    # TC-501: デフォルトリセット
    def test_reset_to_default(self):
        """設定がデフォルト値にリセットされる"""
        # カスタム設定を保存
        custom_config = {"app_path": "custom.exe", "icon_size": 64}
        self.manager.save_config(custom_config)
        
        # デフォルトにリセット
        result = self.manager.reset_to_default()
        assert result is True
        
        # リセット確認
        current_config = self.manager.load_config()
        default_config = self.manager.get_default_config()
        assert current_config == default_config

    # TC-701: 読み込み速度テスト
    def test_load_performance(self):
        """設定読み込みが100ms以内に完了する"""
        # テスト用設定ファイル作成
        test_config = self.manager.get_default_config()
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        start_time = time.time()
        self.manager.load_config()
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # ミリ秒
        assert execution_time < 100, f"読み込み時間が{execution_time:.2f}msで100msを超えています"

    # TC-702: 保存速度テスト
    def test_save_performance(self):
        """設定保存が500ms以内に完了する"""
        test_config = self.manager.get_default_config()
        
        start_time = time.time()
        self.manager.save_config(test_config)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # ミリ秒
        assert execution_time < 500, f"保存時間が{execution_time:.2f}msで500msを超えています"

    # TC-801: ファイル改ざん検知
    @pytest.mark.skip(reason="ハッシュチェック機能は後の段階で実装予定")
    def test_file_tampering_detection(self):
        """設定ファイルの改ざんが検知される"""
        # この機能は要件に含まれているが、まず基本機能を完成させる
        pass