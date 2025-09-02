"""
システムトレイ統合機能 テストケース
"""
import os
import tempfile
import time
import threading
from dataclasses import dataclass
from typing import Optional, Callable, Dict, List
from unittest.mock import patch, MagicMock, Mock

import pytest

from src.system_tray import SystemTray, SystemTrayManager, TrayMenuItem


class TestSystemTray:
    """SystemTray クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # TC-001: SystemTray初期化
    def test_system_tray_initialization(self):
        """SystemTrayが正常に初期化される"""
        tray = SystemTray("テストアプリ")
        
        assert tray is not None
        assert hasattr(tray, 'show')
        assert hasattr(tray, 'hide')
        assert hasattr(tray, 'is_visible')
        assert hasattr(tray, 'update_menu')
        assert hasattr(tray, 'add_menu_item')
        assert hasattr(tray, 'remove_menu_item')
        assert hasattr(tray, 'set_callback')
        assert hasattr(tray, 'show_notification')
        assert tray.app_name == "テストアプリ"

    # TC-002: トレイアイコン表示
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.pystray')
    def test_show_tray_icon(self, mock_pystray):
        """トレイアイコンが正常に表示される"""
        mock_icon = Mock()
        mock_pystray.Icon.return_value = mock_icon
        
        tray = SystemTray()
        result = tray.show()
        
        assert result is True
        assert tray.is_visible() is True
        mock_pystray.Icon.assert_called_once()

    # TC-003: トレイアイコン非表示
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.pystray')
    def test_hide_tray_icon(self, mock_pystray):
        """トレイアイコンが正常に非表示になる"""
        mock_icon = Mock()
        mock_pystray.Icon.return_value = mock_icon
        
        tray = SystemTray()
        tray.show()
        tray.hide()
        
        assert tray.is_visible() is False
        mock_icon.stop.assert_called_once()

    # TC-004: システムトレイが利用できない場合
    @patch('src.system_tray.TRAY_AVAILABLE', False)
    def test_tray_not_available(self):
        """システムトレイが利用できない場合の処理"""
        tray = SystemTray()
        result = tray.show()
        
        assert result is False
        assert tray.is_visible() is False

    # TC-101: メニュー項目追加
    def test_add_menu_item(self):
        """メニュー項目が正しく追加される"""
        tray = SystemTray()
        
        def test_action():
            pass
        
        item = TrayMenuItem("テスト項目", test_action)
        tray.add_menu_item(item)
        
        # メニューアイテムが追加されることを確認
        assert len(tray._menu_items) > 3  # デフォルトの3項目 + 1

    # TC-102: メニュー項目削除
    def test_remove_menu_item(self):
        """メニュー項目が正しく削除される"""
        tray = SystemTray()
        
        # テスト項目を追加
        item = TrayMenuItem("削除テスト", lambda: None)
        tray.add_menu_item(item)
        
        # 削除
        result = tray.remove_menu_item("削除テスト")
        
        assert result is True
        # 削除されたことを確認
        for menu_item in tray._menu_items:
            assert menu_item.title != "削除テスト"

    # TC-103: 存在しないメニュー項目の削除
    def test_remove_nonexistent_menu_item(self):
        """存在しないメニュー項目の削除が適切に処理される"""
        tray = SystemTray()
        
        result = tray.remove_menu_item("存在しない項目")
        
        assert result is False

    # TC-201: コールバック設定
    def test_set_callback(self):
        """イベントコールバックが正しく設定される"""
        tray = SystemTray()
        
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        tray.set_callback('test_event', test_callback)
        
        # コールバックが設定されることを確認
        assert 'test_event' in tray._callbacks
        assert tray._callbacks['test_event'] == test_callback

    # TC-202: 設定メニュークリック
    @patch('src.system_tray.tk')
    def test_settings_menu_click(self, mock_tk):
        """設定メニューのクリック処理"""
        mock_root = Mock()
        mock_tk._default_root = mock_root
        
        tray = SystemTray()
        
        settings_called = False
        
        def settings_callback():
            nonlocal settings_called
            settings_called = True
        
        tray.set_callback('settings', settings_callback)
        tray._on_settings()
        
        # コールバックがスケジュールされることを確認
        mock_root.after.assert_called_once()

    # TC-203: 終了メニュークリック
    @patch('src.system_tray.tk')
    def test_exit_menu_click(self, mock_tk):
        """終了メニューのクリック処理"""
        mock_root = Mock()
        mock_tk._default_root = mock_root
        
        tray = SystemTray()
        
        exit_called = False
        
        def exit_callback():
            nonlocal exit_called
            exit_called = True
        
        tray.set_callback('exit', exit_callback)
        tray._on_exit()
        
        # コールバックがスケジュールされることを確認
        mock_root.after.assert_called_once()

    # TC-301: アイコン画像作成
    @patch('src.system_tray.Image')
    @patch('src.system_tray.ImageDraw')
    def test_create_icon_image(self, mock_image_draw, mock_image):
        """トレイアイコン画像が正しく作成される"""
        mock_img = Mock()
        mock_draw = Mock()
        mock_image.new.return_value = mock_img
        mock_image_draw.Draw.return_value = mock_draw
        
        tray = SystemTray()
        result = tray._create_icon_image()
        
        # 画像が作成されることを確認
        mock_image.new.assert_called_once()
        mock_image_draw.Draw.assert_called_once_with(mock_img)
        mock_draw.ellipse.assert_called_once()
        assert result == mock_img

    # TC-302: アイコン画像作成エラー処理
    @patch('src.system_tray.Image')
    def test_create_icon_image_error_handling(self, mock_image):
        """アイコン画像作成時のエラーが適切に処理される"""
        # 例外を発生させる
        mock_image.new.side_effect = Exception("Image creation failed")
        
        tray = SystemTray()
        result = tray._create_icon_image()
        
        # フォールバック画像が作成されることを確認
        assert result is not None

    # TC-401: 通知表示
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.pystray')
    def test_show_notification(self, mock_pystray):
        """通知が正常に表示される"""
        mock_icon = Mock()
        mock_pystray.Icon.return_value = mock_icon
        
        tray = SystemTray()
        tray.show()
        tray.show_notification("テストタイトル", "テストメッセージ", 5)
        
        # 通知が表示されることを確認
        mock_icon.notify.assert_called_once_with("テストメッセージ", "テストタイトル")

    # TC-402: 非表示時の通知表示
    def test_show_notification_when_hidden(self):
        """非表示時の通知表示が適切に処理される"""
        tray = SystemTray()
        
        # 例外が発生しないことを確認
        try:
            tray.show_notification("テスト", "メッセージ")
            assert True
        except Exception:
            pytest.fail("非表示時の通知でエラーが発生しました")

    # TC-501: メニュー更新
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.pystray')
    def test_update_menu(self, mock_pystray):
        """メニューが正しく更新される"""
        mock_icon = Mock()
        mock_pystray.Icon.return_value = mock_icon
        
        tray = SystemTray()
        tray.show()
        
        # 新しいメニューアイテム
        new_items = [
            TrayMenuItem("新項目1", lambda: None),
            TrayMenuItem("新項目2", lambda: None),
            TrayMenuItem("", separator=True),
            TrayMenuItem("終了", lambda: None)
        ]
        
        tray.update_menu(new_items)
        
        assert len(tray._menu_items) == 4


class TestSystemTrayManager:
    """SystemTrayManager クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # TC-001: SystemTrayManager初期化
    def test_system_tray_manager_initialization(self):
        """SystemTrayManagerが正常に初期化される"""
        manager = SystemTrayManager("テストマネージャー")
        
        assert manager is not None
        assert hasattr(manager, 'initialize')
        assert hasattr(manager, 'start')
        assert hasattr(manager, 'stop')
        assert hasattr(manager, 'is_running')
        assert hasattr(manager, 'set_callbacks')
        assert hasattr(manager, 'add_menu_item')
        assert hasattr(manager, 'notify')
        assert hasattr(manager, 'set_enabled')
        assert hasattr(manager, 'is_available')
        assert hasattr(manager, 'get_status')
        assert manager.app_name == "テストマネージャー"

    # TC-002: 初期化処理
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    def test_initialize(self):
        """初期化処理が正常に実行される"""
        manager = SystemTrayManager()
        result = manager.initialize()
        
        assert result is True
        assert manager._tray is not None

    # TC-003: システムトレイ利用不可時の初期化
    @patch('src.system_tray.TRAY_AVAILABLE', False)
    def test_initialize_not_available(self):
        """システムトレイが利用できない時の初期化処理"""
        manager = SystemTrayManager()
        result = manager.initialize()
        
        assert result is False

    # TC-101: 開始・停止処理
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.pystray')
    def test_start_stop(self, mock_pystray):
        """開始・停止処理が正常に動作する"""
        mock_icon = Mock()
        mock_pystray.Icon.return_value = mock_icon
        
        manager = SystemTrayManager()
        manager.initialize()
        
        # 開始
        start_result = manager.start()
        assert start_result is True
        assert manager.is_running() is True
        
        # 停止
        manager.stop()
        assert manager.is_running() is False

    # TC-102: 無効化時の開始処理
    def test_start_when_disabled(self):
        """無効化されている時の開始処理"""
        manager = SystemTrayManager()
        manager.set_enabled(False)
        manager.initialize()
        
        result = manager.start()
        assert result is False

    # TC-201: コールバック設定
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    def test_set_callbacks(self):
        """コールバックが正しく設定される"""
        manager = SystemTrayManager()
        manager.initialize()
        
        callbacks = {
            'settings': lambda: None,
            'exit': lambda: None
        }
        
        manager.set_callbacks(callbacks)
        
        # コールバックが設定されることを確認
        assert manager._tray._callbacks['settings'] == callbacks['settings']
        assert manager._tray._callbacks['exit'] == callbacks['exit']

    # TC-202: メニューアイテム追加
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    def test_add_menu_item(self):
        """メニューアイテムが正しく追加される"""
        manager = SystemTrayManager()
        manager.initialize()
        
        def test_action():
            pass
        
        manager.add_menu_item("テスト項目", test_action)
        
        # メニューアイテムが追加されることを確認
        found = False
        for item in manager._tray._menu_items:
            if item.title == "テスト項目":
                found = True
                break
        
        assert found is True

    # TC-301: 通知表示
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.pystray')
    def test_notify(self, mock_pystray):
        """通知が正常に表示される"""
        mock_icon = Mock()
        mock_pystray.Icon.return_value = mock_icon
        
        manager = SystemTrayManager()
        manager.initialize()
        manager.start()
        
        manager.notify("テストタイトル", "テストメッセージ", 3)
        
        # 通知が表示されることを確認
        mock_icon.notify.assert_called_once_with("テストメッセージ", "テストタイトル")

    # TC-401: 有効/無効設定
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.pystray')
    def test_set_enabled(self, mock_pystray):
        """有効/無効設定が正常に動作する"""
        mock_icon = Mock()
        mock_pystray.Icon.return_value = mock_icon
        
        manager = SystemTrayManager()
        manager.initialize()
        manager.start()
        
        # 無効化
        manager.set_enabled(False)
        assert manager._enabled is False
        
        # 有効化
        manager.set_enabled(True)
        assert manager._enabled is True

    # TC-402: ステータス取得
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    def test_get_status(self):
        """ステータス情報が正しく取得される"""
        manager = SystemTrayManager("ステータステスト")
        manager.initialize()
        
        status = manager.get_status()
        
        assert isinstance(status, dict)
        assert 'available' in status
        assert 'enabled' in status
        assert 'running' in status
        assert 'app_name' in status
        assert status['app_name'] == "ステータステスト"
        assert status['available'] is True


class TestTrayMenuItem:
    """TrayMenuItem データクラスのテストケース"""

    # TC-001: TrayMenuItem作成
    def test_tray_menu_item_creation(self):
        """TrayMenuItemが正常に作成される"""
        def test_action():
            pass
        
        item = TrayMenuItem("テスト項目", test_action, True, True, False)
        
        assert item.title == "テスト項目"
        assert item.action == test_action
        assert item.checked is True
        assert item.enabled is True
        assert item.separator is False

    # TC-002: デフォルト値
    def test_tray_menu_item_defaults(self):
        """TrayMenuItemのデフォルト値が正しい"""
        item = TrayMenuItem("テスト")
        
        assert item.title == "テスト"
        assert item.action is None
        assert item.checked is False
        assert item.enabled is True
        assert item.separator is False

    # TC-003: セパレーター項目
    def test_separator_item(self):
        """セパレーター項目が正しく作成される"""
        item = TrayMenuItem("", separator=True)
        
        assert item.title == ""
        assert item.separator is True


class TestErrorHandling:
    """エラーハンドリングのテストケース"""

    # TC-001: 例外処理
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.pystray')
    def test_exception_handling(self, mock_pystray):
        """各種例外が適切に処理される"""
        # pystray.Icon で例外が発生する状況をシミュレート
        mock_pystray.Icon.side_effect = Exception("Tray creation failed")
        
        tray = SystemTray()
        
        # 例外が適切に処理されることを確認
        try:
            result = tray.show()
            assert result is False
            assert tray.is_visible() is False
        except Exception:
            pytest.fail("例外が適切に処理されていません")

    # TC-002: スレッドエラー処理
    @patch('src.system_tray.TRAY_AVAILABLE', True)
    @patch('src.system_tray.threading.Thread')
    def test_thread_error_handling(self, mock_thread):
        """スレッド関連エラーが適切に処理される"""
        # Thread作成で例外が発生
        mock_thread.side_effect = Exception("Thread creation failed")
        
        tray = SystemTray()
        
        # 例外が適切に処理されることを確認
        try:
            result = tray.show()
            # エラーが発生しても継続することを確認
            assert isinstance(result, bool)
        except Exception:
            pytest.fail("スレッドエラーが適切に処理されていません")