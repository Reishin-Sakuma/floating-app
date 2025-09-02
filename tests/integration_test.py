"""
統合テスト: FloatingIconとAppLauncherの連携テスト
"""
import os
import tempfile
import time
from unittest.mock import Mock, patch

import pytest

from src.config_manager import ConfigManager
from src.app_launcher import AppLauncher
from src.floating_icon import FloatingIcon


class TestIntegration:
    """統合テスト"""

    def setup_method(self):
        """テスト準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager()
        self.app_launcher = AppLauncher()
        
        # テスト用設定
        self.test_config = {
            'app_path': 'C:\\Windows\\System32\\notepad.exe',
            'icon_position': {'x': 200, 'y': 150},
            'icon_size': 48,
            'auto_start': True
        }
        self.config_manager.save_config(self.test_config)

    def teardown_method(self):
        """テスト後処理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.floating_icon.tk.Canvas')
    @patch('src.floating_icon.tk.Toplevel')
    def test_floating_icon_with_app_launcher_integration(self, mock_toplevel, mock_canvas):
        """FloatingIconとAppLauncherの統合動作"""
        # Arrange
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance
        
        launch_called = False
        launched_path = None
        
        def mock_launch_app():
            nonlocal launch_called, launched_path
            launch_called = True
            # 実際の設定から起動パスを取得
            config = self.config_manager.load_config()
            launched_path = config.get('app_path')
        
        # Act
        floating_icon = FloatingIcon(self.config_manager)
        floating_icon.set_click_callback(mock_launch_app)
        
        # FloatingIconを表示
        result = floating_icon.show()
        assert result is True
        
        # 設定が正しく読み込まれているかチェック
        position = floating_icon.get_position()
        size = floating_icon.get_size()
        assert position == (200, 150)
        assert size == 48
        
        # クリックイベントをシミュレート
        floating_icon._handle_left_click(None)
        
        # Assert
        assert launch_called is True
        assert launched_path == 'C:\\Windows\\System32\\notepad.exe'

    @patch('src.floating_icon.tk.Canvas')
    @patch('src.floating_icon.tk.Toplevel')
    def test_config_manager_integration_with_all_components(self, mock_toplevel, mock_canvas):
        """ConfigManager、AppLauncher、FloatingIconの統合動作"""
        # Arrange
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance
        
        # Act
        floating_icon = FloatingIcon(self.config_manager)
        app_launcher = AppLauncher()
        
        # 設定から値を読み込み
        config = self.config_manager.load_config()
        app_path = config['app_path']
        
        # FloatingIconが設定を正しく読み込んでいるかテスト
        assert floating_icon.get_position() == (200, 150)
        assert floating_icon.get_size() == 48
        
        # AppLauncherで設定のアプリケーションパスを検証
        is_valid = app_launcher.is_valid_executable(app_path)
        assert is_valid is True
        
        # 実際の統合: FloatingIcon -> AppLauncher起動
        def integrated_launch():
            return app_launcher.launch_application(app_path)
        
        floating_icon.set_click_callback(integrated_launch)
        
        # テスト実行
        floating_icon.show()
        
        # Assert - コンポーネント間の統合が成功
        assert True  # 例外なく実行完了

    @patch('src.floating_icon.tk.Canvas') 
    @patch('src.floating_icon.tk.Toplevel')
    def test_position_persistence_across_sessions(self, mock_toplevel, mock_canvas):
        """セッション間での位置保持テスト"""
        # Arrange
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance
        
        # セッション1: 位置変更
        icon1 = FloatingIcon(self.config_manager)
        icon1.update_position(300, 250)
        
        # 設定に保存されたかチェック（実装で_save_position_to_configが呼ばれることを想定）
        icon1._save_position_to_config()
        
        # セッション2: 新しいインスタンスで位置復元
        icon2 = FloatingIcon(self.config_manager)
        position = icon2.get_position()
        
        # Assert
        assert position == (300, 250)

    @patch('subprocess.Popen')
    @patch('src.floating_icon.tk.Canvas')
    @patch('src.floating_icon.tk.Toplevel') 
    def test_end_to_end_workflow(self, mock_toplevel, mock_canvas, mock_popen):
        """エンドツーエンドワークフローテスト"""
        # Arrange
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance
        
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # Act: 完全なワークフロー
        # 1. ConfigManagerから設定読み込み
        config = self.config_manager.load_config()
        
        # 2. FloatingIcon初期化（設定適用）
        floating_icon = FloatingIcon(self.config_manager)
        
        # 3. AppLauncher初期化
        app_launcher = AppLauncher()
        
        # 4. FloatingIconにAppLauncher連携設定
        app_path = config['app_path']
        
        def launch_configured_app():
            return app_launcher.launch_application(app_path)
        
        floating_icon.set_click_callback(launch_configured_app)
        
        # 5. FloatingIcon表示
        show_result = floating_icon.show()
        
        # 6. ユーザークリックシミュレート
        floating_icon._handle_left_click(None)
        
        # Assert
        assert show_result is True
        assert floating_icon.is_visible() is True
        mock_popen.assert_called_once()
        
        # 起動したアプリケーションのパスが正しいかチェック
        call_args = mock_popen.call_args[0][0]
        assert app_path in call_args

    def test_error_recovery_integration(self):
        """エラー回復統合テスト"""
        # 破損した設定ファイルでの動作確認
        config_manager = ConfigManager()
        
        # 意図的に無効な設定を作成
        invalid_config = {
            'app_path': 'invalid_path.exe',
            'icon_position': {'x': 'invalid', 'y': -1000},
            'icon_size': -50
        }
        config_manager.save_config(invalid_config)
        
        # FloatingIconが適切にデフォルト値で動作するかテスト
        with patch('src.floating_icon.tk.Canvas'), \
             patch('src.floating_icon.tk.Toplevel') as mock_toplevel:
            
            mock_window = Mock()
            mock_toplevel.return_value = mock_window
            
            # 例外なく初期化できることを確認
            floating_icon = FloatingIcon(config_manager)
            
            # デフォルト値で動作することを確認
            position = floating_icon.get_position()
            size = floating_icon.get_size()
            
            assert isinstance(position, tuple)
            assert isinstance(size, int)
            assert position[0] >= 0
            assert position[1] >= 0
            assert size > 0