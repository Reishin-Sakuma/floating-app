"""
Windows自動起動機能 テストケース
"""
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, Mock
from dataclasses import dataclass

import pytest

from src.auto_startup import WindowsAutoStartup, AutoStartupManager, AutoStartupInfo


class TestWindowsAutoStartup:
    """WindowsAutoStartup クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # TC-001: WindowsAutoStartup初期化
    def test_windows_auto_startup_initialization(self):
        """WindowsAutoStartupが正常に初期化される"""
        startup = WindowsAutoStartup("TestApp")
        
        assert startup is not None
        assert hasattr(startup, 'is_enabled')
        assert hasattr(startup, 'enable')
        assert hasattr(startup, 'disable')
        assert hasattr(startup, 'get_info')
        assert hasattr(startup, 'toggle')
        assert hasattr(startup, 'validate_path')
        assert startup.app_name == "TestApp"
        assert startup.STARTUP_KEY == r"Software\Microsoft\Windows\CurrentVersion\Run"

    # TC-002: 自動起動有効化
    @patch('src.auto_startup.winreg')
    def test_enable_auto_startup(self, mock_winreg):
        """自動起動が正常に有効化される"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = 0x00000002
        mock_winreg.REG_SZ = 1
        
        startup = WindowsAutoStartup("TestApp")
        success, error = startup.enable()
        
        assert success is True
        assert error is None
        mock_winreg.SetValueEx.assert_called_once()

    # TC-003: 自動起動無効化
    @patch('src.auto_startup.winreg')
    def test_disable_auto_startup(self, mock_winreg):
        """自動起動が正常に無効化される"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = 0x00000002
        
        startup = WindowsAutoStartup("TestApp")
        success, error = startup.disable()
        
        assert success is True
        assert error is None
        mock_winreg.DeleteValue.assert_called_once_with(mock_key, "TestApp")

    # TC-004: 自動起動状態確認（有効）
    @patch('src.auto_startup.winreg')
    def test_is_enabled_true(self, mock_winreg):
        """自動起動が有効な場合の状態確認"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        
        startup = WindowsAutoStartup("TestApp")
        # パスを設定
        startup._app_path = "C:\\test\\app.exe"
        
        # 同じパスを返すように設定
        mock_winreg.QueryValueEx.return_value = ("C:\\test\\app.exe", None)
        
        enabled, error = startup.is_enabled()
        
        assert enabled is True
        assert error is None

    # TC-005: 自動起動状態確認（無効）
    @patch('src.auto_startup.winreg')
    def test_is_enabled_false(self, mock_winreg):
        """自動起動が無効な場合の状態確認"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.QueryValueEx.side_effect = FileNotFoundError()
        
        startup = WindowsAutoStartup("TestApp")
        enabled, error = startup.is_enabled()
        
        assert enabled is False
        assert error is None

    # TC-101: レジストリアクセスエラー処理
    @patch('src.auto_startup.winreg')
    def test_registry_access_error(self, mock_winreg):
        """レジストリアクセスエラーが適切に処理される"""
        mock_winreg.OpenKey.side_effect = Exception("Registry access denied")
        
        startup = WindowsAutoStartup("TestApp")
        enabled, error = startup.is_enabled()
        
        assert enabled is False
        assert error is not None
        assert "レジストリアクセスエラー" in error

    # TC-102: 有効化エラー処理
    @patch('src.auto_startup.winreg')
    def test_enable_error_handling(self, mock_winreg):
        """有効化時のエラーが適切に処理される"""
        mock_winreg.OpenKey.side_effect = Exception("Permission denied")
        
        startup = WindowsAutoStartup("TestApp")
        success, error = startup.enable()
        
        assert success is False
        assert error is not None
        assert "自動起動の有効化に失敗" in error

    # TC-103: 無効化エラー処理
    @patch('src.auto_startup.winreg')
    def test_disable_error_handling(self, mock_winreg):
        """無効化時のエラーが適切に処理される"""
        mock_winreg.OpenKey.side_effect = Exception("Permission denied")
        
        startup = WindowsAutoStartup("TestApp")
        success, error = startup.disable()
        
        assert success is False
        assert error is not None
        assert "自動起動の無効化に失敗" in error

    # TC-201: 自動起動切り替え（有効→無効）
    @patch('src.auto_startup.winreg')
    def test_toggle_enabled_to_disabled(self, mock_winreg):
        """自動起動を有効→無効に切り替え"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = 0x00000002
        
        startup = WindowsAutoStartup("TestApp")
        startup._app_path = "C:\\test\\app.exe"
        
        # 最初は有効状態
        mock_winreg.QueryValueEx.return_value = ("C:\\test\\app.exe", None)
        
        success, new_state, error = startup.toggle()
        
        assert success is True
        assert new_state is False  # 無効化された
        assert error is None

    # TC-202: 自動起動切り替え（無効→有効）
    @patch('src.auto_startup.winreg')
    def test_toggle_disabled_to_enabled(self, mock_winreg):
        """自動起動を無効→有効に切り替え"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = 0x00000002
        mock_winreg.REG_SZ = 1
        
        startup = WindowsAutoStartup("TestApp")
        
        # 最初は無効状態
        mock_winreg.QueryValueEx.side_effect = FileNotFoundError()
        
        success, new_state, error = startup.toggle()
        
        assert success is True
        assert new_state is True  # 有効化された
        assert error is None

    # TC-301: 実行ファイルパス取得（PyInstaller）
    @patch('src.auto_startup.sys')
    def test_get_executable_path_pyinstaller(self, mock_sys):
        """PyInstaller環境での実行ファイルパス取得"""
        mock_sys._MEIPASS = "/tmp/pyinstaller"
        mock_sys.executable = "C:\\dist\\app.exe"
        
        startup = WindowsAutoStartup("TestApp")
        path = startup._get_current_executable_path()
        
        assert path == "C:\\dist\\app.exe"

    # TC-302: 実行ファイルパス取得（Pythonスクリプト）
    @patch('src.auto_startup.sys')
    @patch('src.auto_startup.os.path.abspath')
    def test_get_executable_path_python_script(self, mock_abspath, mock_sys):
        """Pythonスクリプト環境での実行ファイルパス取得"""
        # _MEIPASSが存在しない（PyInstallerではない）
        del mock_sys._MEIPASS if hasattr(mock_sys, '_MEIPASS') else None
        mock_sys.argv = ["test_script.py"]
        mock_sys.executable = "C:\\Python\\python.exe"
        mock_abspath.return_value = "C:\\project\\test_script.py"
        
        startup = WindowsAutoStartup("TestApp")
        path = startup._get_current_executable_path()
        
        expected = '"C:\\Python\\python.exe" "C:\\project\\test_script.py"'
        assert path == expected

    # TC-401: パス検証（有効なパス）
    @patch('src.auto_startup.os.path.exists')
    @patch('src.auto_startup.os.path.isfile')
    def test_validate_path_valid(self, mock_isfile, mock_exists):
        """有効なパスの検証"""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        startup = WindowsAutoStartup("TestApp")
        valid, error = startup.validate_path("C:\\test\\app.exe")
        
        assert valid is True
        assert error is None

    # TC-402: パス検証（存在しないパス）
    @patch('src.auto_startup.os.path.exists')
    def test_validate_path_not_exists(self, mock_exists):
        """存在しないパスの検証"""
        mock_exists.return_value = False
        
        startup = WindowsAutoStartup("TestApp")
        valid, error = startup.validate_path("C:\\nonexistent\\app.exe")
        
        assert valid is False
        assert error is not None
        assert "ファイルが見つかりません" in error

    # TC-403: パス検証（Pythonコマンドライン）
    @patch('src.auto_startup.os.path.exists')
    def test_validate_path_python_command(self, mock_exists):
        """Pythonコマンドラインの検証"""
        mock_exists.return_value = True
        
        startup = WindowsAutoStartup("TestApp")
        path = '"C:\\Python\\python.exe" "C:\\project\\script.py"'
        valid, error = startup.validate_path(path)
        
        assert valid is True
        assert error is None

    # TC-501: 自動起動情報取得
    @patch('src.auto_startup.winreg')
    def test_get_info(self, mock_winreg):
        """自動起動情報の取得"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        
        startup = WindowsAutoStartup("TestApp")
        startup._app_path = "C:\\test\\app.exe"
        mock_winreg.QueryValueEx.return_value = ("C:\\test\\app.exe", None)
        
        info = startup.get_info()
        
        assert isinstance(info, AutoStartupInfo)
        assert info.enabled is True
        assert info.app_name == "TestApp"
        assert info.app_path == "C:\\test\\app.exe"
        assert info.registry_key == r"Software\Microsoft\Windows\CurrentVersion\Run"
        assert info.error is None


class TestAutoStartupManager:
    """AutoStartupManager クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # TC-001: AutoStartupManager初期化
    def test_auto_startup_manager_initialization(self):
        """AutoStartupManagerが正常に初期化される"""
        manager = AutoStartupManager("TestApp")
        
        assert manager is not None
        assert hasattr(manager, 'is_supported')
        assert hasattr(manager, 'get_status')
        assert hasattr(manager, 'set_enabled')
        assert hasattr(manager, 'toggle_startup')
        assert hasattr(manager, 'validate_installation')
        assert hasattr(manager, 'repair_startup')
        assert manager.app_name == "TestApp"

    # TC-002: Windowsサポート確認
    @patch('src.auto_startup.os.name', 'nt')
    def test_is_supported_windows(self):
        """Windows環境でのサポート確認"""
        manager = AutoStartupManager()
        
        assert manager.is_supported() is True

    # TC-003: 非Windowsサポート確認
    @patch('src.auto_startup.os.name', 'posix')
    def test_is_supported_non_windows(self):
        """非Windows環境でのサポート確認"""
        manager = AutoStartupManager()
        
        assert manager.is_supported() is False

    # TC-101: 自動起動設定（有効化）
    @patch('src.auto_startup.os.name', 'nt')
    @patch('src.auto_startup.winreg')
    def test_set_enabled_true(self, mock_winreg):
        """自動起動の有効化"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = 0x00000002
        mock_winreg.REG_SZ = 1
        
        # 最初は無効状態
        mock_winreg.QueryValueEx.side_effect = FileNotFoundError()
        
        manager = AutoStartupManager("TestApp")
        success, error = manager.set_enabled(True)
        
        assert success is True
        assert error is None

    # TC-102: 自動起動設定（無効化）
    @patch('src.auto_startup.os.name', 'nt')
    @patch('src.auto_startup.winreg')
    def test_set_enabled_false(self, mock_winreg):
        """自動起動の無効化"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = 0x00000002
        
        manager = AutoStartupManager("TestApp")
        manager._startup._app_path = "C:\\test\\app.exe"
        
        # 最初は有効状態
        mock_winreg.QueryValueEx.return_value = ("C:\\test\\app.exe", None)
        
        success, error = manager.set_enabled(False)
        
        assert success is True
        assert error is None

    # TC-103: 非Windows環境での設定
    @patch('src.auto_startup.os.name', 'posix')
    def test_set_enabled_unsupported_os(self):
        """非Windows環境での自動起動設定"""
        manager = AutoStartupManager("TestApp")
        success, error = manager.set_enabled(True)
        
        assert success is False
        assert error is not None
        assert "Windowsでのみサポート" in error

    # TC-201: ステータス取得（Windows）
    @patch('src.auto_startup.os.name', 'nt')
    @patch('src.auto_startup.winreg')
    def test_get_status_windows(self, mock_winreg):
        """Windows環境でのステータス取得"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        
        manager = AutoStartupManager("TestApp")
        manager._startup._app_path = "C:\\test\\app.exe"
        mock_winreg.QueryValueEx.return_value = ("C:\\test\\app.exe", None)
        
        status = manager.get_status()
        
        assert isinstance(status, AutoStartupInfo)
        assert status.enabled is True
        assert status.app_name == "TestApp"
        assert status.error is None

    # TC-202: ステータス取得（非Windows）
    @patch('src.auto_startup.os.name', 'posix')
    def test_get_status_non_windows(self):
        """非Windows環境でのステータス取得"""
        manager = AutoStartupManager("TestApp")
        
        status = manager.get_status()
        
        assert isinstance(status, AutoStartupInfo)
        assert status.enabled is False
        assert status.app_name == "TestApp"
        assert status.error == "Windowsでのみサポートされています"

    # TC-301: 自動起動切り替え
    @patch('src.auto_startup.os.name', 'nt')
    @patch('src.auto_startup.winreg')
    def test_toggle_startup(self, mock_winreg):
        """自動起動の切り替え"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = 0x00000002
        mock_winreg.REG_SZ = 1
        
        # 最初は無効状態
        mock_winreg.QueryValueEx.side_effect = FileNotFoundError()
        
        manager = AutoStartupManager("TestApp")
        success, new_state, error = manager.toggle_startup()
        
        assert success is True
        assert new_state is True  # 有効化された
        assert error is None

    # TC-401: インストール検証
    @patch('src.auto_startup.os.name', 'nt')
    @patch('src.auto_startup.winreg')
    @patch('src.auto_startup.os.path.exists')
    @patch('src.auto_startup.os.path.isfile')
    def test_validate_installation(self, mock_isfile, mock_exists, mock_winreg):
        """インストール状態の検証"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        manager = AutoStartupManager("TestApp")
        manager._startup._app_path = "C:\\test\\app.exe"
        mock_winreg.QueryValueEx.return_value = ("C:\\test\\app.exe", None)
        
        valid, error = manager.validate_installation()
        
        assert valid is True
        assert error is None

    # TC-402: 自動起動修復
    @patch('src.auto_startup.os.name', 'nt')
    @patch('src.auto_startup.winreg')
    def test_repair_startup(self, mock_winreg):
        """自動起動設定の修復"""
        mock_key = Mock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
        mock_winreg.KEY_SET_VALUE = 0x00000002
        mock_winreg.REG_SZ = 1
        
        manager = AutoStartupManager("TestApp")
        manager._startup._app_path = "C:\\test\\app.exe"
        
        # 有効状態
        mock_winreg.QueryValueEx.return_value = ("C:\\test\\app.exe", None)
        
        success, message = manager.repair_startup()
        
        assert success is True
        assert message is not None
        assert "修復" in message