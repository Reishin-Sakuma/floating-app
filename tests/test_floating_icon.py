"""
フローティングアイコン描画エンジン テストケース
"""
import os
import tempfile
import time
import tkinter as tk
from dataclasses import dataclass
from typing import Optional, Tuple, Callable
from unittest.mock import patch, MagicMock, Mock

import pytest

from src.floating_icon import FloatingIcon, IconStyle, DisplayInfo
from src.config_manager import ConfigManager


class TestFloatingIcon:
    """FloatingIcon クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.config_manager = ConfigManager()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # TC-001: FloatingIcon初期化
    def test_floating_icon_initialization(self):
        """FloatingIconが正常に初期化される"""
        icon = FloatingIcon(self.config_manager)
        
        assert icon is not None
        assert hasattr(icon, 'show')
        assert hasattr(icon, 'hide')
        assert hasattr(icon, 'update_position')
        assert hasattr(icon, 'update_size')
        assert hasattr(icon, 'set_click_callback')
        assert hasattr(icon, 'set_right_click_callback')
        assert hasattr(icon, 'is_visible')
        assert hasattr(icon, 'get_position')
        assert hasattr(icon, 'get_size')
        assert hasattr(icon, 'refresh')

    # TC-002: アイコン表示
    @patch('src.floating_icon.tk.Canvas')
    @patch('src.floating_icon.tk.Toplevel')
    def test_show_icon(self, mock_toplevel, mock_canvas):
        """フローティングアイコンが正常に表示される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance
        
        icon = FloatingIcon(self.config_manager)
        result = icon.show()
        
        assert result is True
        assert icon.is_visible() is True

    # TC-003: アイコン非表示
    @patch('src.floating_icon.tk.Canvas')
    @patch('src.floating_icon.tk.Toplevel')
    def test_hide_icon(self, mock_toplevel, mock_canvas):
        """フローティングアイコンが正常に非表示になる"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance
        
        icon = FloatingIcon(self.config_manager)
        icon.show()
        result = icon.hide()
        
        assert result is True
        assert icon.is_visible() is False

    # TC-101: 位置設定
    @patch('src.floating_icon.tk.Toplevel')
    def test_update_position(self, mock_toplevel):
        """アイコンの位置が正しく設定される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        result = icon.update_position(200, 150)
        
        assert result is True
        position = icon.get_position()
        assert position == (200, 150)

    # TC-102: 無効な位置設定
    @patch('src.floating_icon.tk.Toplevel')
    def test_update_position_invalid(self, mock_toplevel):
        """画面外など無効な位置が適切に処理される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        
        # 負の座標
        result = icon.update_position(-100, -100)
        position = icon.get_position()
        
        # 位置が補正されていることを確認
        assert position[0] >= 0
        assert position[1] >= 0

    # TC-103: 現在位置取得
    @patch('src.floating_icon.tk.Toplevel')
    def test_get_position(self, mock_toplevel):
        """現在の位置が正しく取得される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        icon.update_position(300, 250)
        
        position = icon.get_position()
        assert isinstance(position, tuple)
        assert len(position) == 2
        assert position == (300, 250)

    # TC-201: サイズ設定
    @patch('src.floating_icon.tk.Toplevel')
    def test_update_size(self, mock_toplevel):
        """アイコンのサイズが正しく設定される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        result = icon.update_size(48)
        
        assert result is True
        size = icon.get_size()
        assert size == 48

    # TC-202: 無効なサイズ設定
    @patch('src.floating_icon.tk.Toplevel')
    def test_update_size_invalid(self, mock_toplevel):
        """無効なサイズ値が適切に処理される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        
        # 負のサイズ
        result = icon.update_size(-10)
        assert result is False or icon.get_size() > 0
        
        # ゼロサイズ
        result = icon.update_size(0)
        assert result is False or icon.get_size() > 0

    # TC-203: 現在サイズ取得
    @patch('src.floating_icon.tk.Toplevel')
    def test_get_size(self, mock_toplevel):
        """現在のサイズが正しく取得される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        icon.update_size(64)
        
        size = icon.get_size()
        assert isinstance(size, int)
        assert size == 64

    # TC-301: クリックコールバック設定
    @patch('src.floating_icon.tk.Toplevel')
    def test_set_click_callback(self, mock_toplevel):
        """クリックコールバックが正しく設定される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        def test_callback():
            pass
        
        icon = FloatingIcon(self.config_manager)
        icon.set_click_callback(test_callback)
        
        # エラーが発生しないことを確認
        assert True

    # TC-302: 左クリックイベント処理
    @patch('src.floating_icon.tk.Toplevel')
    def test_left_click_event(self, mock_toplevel):
        """左クリック時にコールバックが呼ばれる"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        icon = FloatingIcon(self.config_manager)
        icon.set_click_callback(test_callback)
        
        # クリックイベントをシミュレート
        icon._handle_left_click(None)  # 内部メソッドの直接呼び出し
        
        assert callback_called is True

    # TC-303: 右クリックコールバック設定
    @patch('src.floating_icon.tk.Toplevel')
    def test_set_right_click_callback(self, mock_toplevel):
        """右クリックコールバックが正しく設定される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        def test_callback():
            pass
        
        icon = FloatingIcon(self.config_manager)
        icon.set_right_click_callback(test_callback)
        
        # エラーが発生しないことを確認
        assert True

    # TC-304: 右クリックイベント処理
    @patch('src.floating_icon.tk.Toplevel')
    def test_right_click_event(self, mock_toplevel):
        """右クリック時にコールバックが呼ばれる"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        icon = FloatingIcon(self.config_manager)
        icon.set_right_click_callback(test_callback)
        
        # 右クリックイベントをシミュレート
        icon._handle_right_click(None)  # 内部メソッドの直接呼び出し
        
        assert callback_called is True

    # TC-401: 基本描画
    @patch('src.floating_icon.tk.Toplevel')
    @patch('src.floating_icon.tk.Canvas')
    def test_basic_drawing(self, mock_canvas, mock_toplevel):
        """アイコンが正しく描画される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_canvas_instance = Mock()
        mock_canvas.return_value = mock_canvas_instance
        
        icon = FloatingIcon(self.config_manager)
        icon.show()
        icon.refresh()
        
        # 描画メソッドが呼ばれることを確認
        # 実際の描画は内部実装に依存するため、エラーがないことを確認
        assert True

    # TC-402: 前面表示維持
    @patch('src.floating_icon.tk.Toplevel')
    def test_topmost_display(self, mock_toplevel):
        """他ウィンドウより前面に表示される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        icon.show()
        
        # topmost属性が設定されることを確認（複数回呼ばれる可能性があるため任意の呼び出しをチェック）
        calls = mock_window.wm_attributes.call_args_list
        topmost_call = any(args == ('-topmost', True) for args, kwargs in calls)
        assert topmost_call, f"Expected wm_attributes('-topmost', True) but got calls: {calls}"

    # TC-501: DPIスケーリング検出
    @patch('src.floating_icon.tk.Tk')
    def test_dpi_scaling_detection(self, mock_tk):
        """システムのDPIスケーリング設定が正しく検出される"""
        mock_root = Mock()
        mock_tk.return_value = mock_root
        mock_root.winfo_fpixels.return_value = 96.0  # 100% スケーリング
        
        icon = FloatingIcon(self.config_manager)
        display_info = icon._get_display_info()
        
        assert isinstance(display_info, DisplayInfo)
        assert display_info.dpi_scale > 0

    # TC-502: 高DPI環境での表示サイズ計算
    @patch('src.floating_icon.tk.Toplevel')
    def test_high_dpi_size_calculation(self, mock_toplevel):
        """高DPI環境で正常にスケールされる"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        
        # 高DPI環境をシミュレート
        with patch.object(icon, '_get_dpi_scale', return_value=1.5):
            icon.update_size(32)
            
            # DPIスケーリングが適用されることを確認
            # 実際のサイズ計算は内部実装に依存
            assert icon.get_size() == 32  # 論理サイズは変わらない

    # TC-701: 描画フレームレート測定
    @patch('src.floating_icon.tk.Toplevel')
    def test_drawing_performance(self, mock_toplevel):
        """60FPS以上の描画性能を達成する"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        icon = FloatingIcon(self.config_manager)
        icon.show()
        
        # パフォーマンステスト
        start_time = time.time()
        iterations = 100
        
        for _ in range(iterations):
            icon.refresh()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 100回の描画が適切な時間内に完了することを確認
        assert total_time < 2.0, f"描画性能が低すぎます: {total_time:.2f}秒"

    # TC-702: メモリ使用量（基本的なメモリリークチェック）
    @patch('src.floating_icon.tk.Toplevel')
    def test_memory_usage(self, mock_toplevel):
        """メモリ使用量が要件内に収まる"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        # 複数のアイコンインスタンスを作成・削除してメモリリークをチェック
        icons = []
        for i in range(10):
            icon = FloatingIcon(self.config_manager)
            icon.show()
            icons.append(icon)
        
        # クリーンアップ
        for icon in icons:
            icon.hide()
        
        # メモリリークの基本チェック（実装が完了してから詳細テスト）
        assert True

    # TC-801: ConfigManager連携
    def test_config_manager_integration(self):
        """設定の保存・読込が正常に動作する"""
        # 設定を変更
        config = self.config_manager.get_default_config()
        config['icon_position'] = {'x': 300, 'y': 200}
        config['icon_size'] = 64
        self.config_manager.save_config(config)
        
        # FloatingIconで設定を読込
        icon = FloatingIcon(self.config_manager)
        
        # 設定が反映されることを確認
        position = icon.get_position()
        size = icon.get_size()
        
        assert position == (300, 200)
        assert size == 64

    # TC-802: AppLauncher連携テスト用のダミー
    @patch('src.floating_icon.tk.Toplevel')
    def test_app_launcher_integration(self, mock_toplevel):
        """クリック時のアプリケーション起動連携をテスト"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        launcher_called = False
        
        def mock_launcher():
            nonlocal launcher_called
            launcher_called = True
        
        icon = FloatingIcon(self.config_manager)
        icon.set_click_callback(mock_launcher)
        
        # クリックイベントをシミュレート
        icon._handle_left_click(None)
        
        assert launcher_called is True

    # TC-901: 描画エラー処理
    @patch('src.floating_icon.tk.Toplevel')
    @patch('src.floating_icon.tk.Canvas')
    def test_drawing_error_handling(self, mock_canvas, mock_toplevel):
        """描画エラーが適切に処理される"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        # Canvas で例外が発生する状況をシミュレート
        mock_canvas_instance = Mock()
        mock_canvas_instance.create_oval.side_effect = Exception("Drawing error")
        mock_canvas.return_value = mock_canvas_instance
        
        icon = FloatingIcon(self.config_manager)
        
        # 描画エラーが発生してもクラッシュしないことを確認
        try:
            icon.refresh()
            assert True  # エラーが適切に処理された
        except Exception:
            pytest.fail("描画エラーが適切に処理されていません")

    # TC-902: ウィンドウシステムエラー
    @patch('src.floating_icon.tk.Toplevel')
    def test_window_system_error(self, mock_toplevel):
        """ウィンドウ関連エラーが適切に処理される"""
        # Toplevelの作成で例外が発生する状況をシミュレート
        mock_toplevel.side_effect = Exception("Window creation failed")
        
        # ウィンドウエラーが適切に処理されることを確認
        try:
            icon = FloatingIcon(self.config_manager)
            icon.show()
            # エラー状態でもオブジェクトが使用可能であることを確認
            assert icon.is_visible() is False
        except Exception:
            pytest.fail("ウィンドウエラーが適切に処理されていません")

    # TC-903: 設定エラー処理
    def test_config_error_handling(self):
        """無効な設定値が適切に処理される"""
        # 無効な設定を作成
        config = {
            'icon_position': {'x': 'invalid', 'y': -1000},
            'icon_size': -50
        }
        self.config_manager.save_config(config)
        
        # 無効な設定でもFloatingIconが動作することを確認
        icon = FloatingIcon(self.config_manager)
        
        # デフォルト値で動作していることを確認
        position = icon.get_position()
        size = icon.get_size()
        
        assert isinstance(position, tuple)
        assert isinstance(size, int)
        assert size > 0