"""
システムトレイ統合機能
"""
import tkinter as tk
from tkinter import messagebox
import threading
import sys
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass

try:
    # Windows用のシステムトレイ実装
    import pystray
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    # pystrayが利用できない場合のフォールバック
    TRAY_AVAILABLE = False
    pystray = None
    Icon = None
    Menu = None
    MenuItem = None
    # PIL用のダミークラス
    class Image:
        @staticmethod
        def new(*args, **kwargs):
            return None
    class ImageDraw:
        @staticmethod
        def Draw(*args, **kwargs):
            return None


@dataclass
class TrayMenuItem:
    """トレイメニュー項目"""
    title: str
    action: Optional[Callable] = None
    checked: bool = False
    enabled: bool = True
    separator: bool = False


class SystemTray:
    """システムトレイ統合クラス"""
    
    def __init__(self, app_name: str = "フローティングランチャー"):
        """システムトレイの初期化"""
        self.app_name = app_name
        self._icon = None
        self._menu_items = []
        self._callbacks = {}
        self._visible = False
        self._thread = None
        
        # デフォルトメニューアイテム
        self._init_default_menu()
    
    def _init_default_menu(self) -> None:
        """デフォルトメニューを初期化"""
        self._menu_items = [
            TrayMenuItem("設定", self._on_settings),
            TrayMenuItem("", separator=True),
            TrayMenuItem("終了", self._on_exit)
        ]
    
    def show(self) -> bool:
        """システムトレイアイコンを表示"""
        if not TRAY_AVAILABLE:
            return False
            
        try:
            if self._visible:
                return True
                
            # アイコン画像を作成
            icon_image = self._create_icon_image()
            
            # メニューを作成
            menu = self._create_menu()
            
            # トレイアイコンを作成
            self._icon = pystray.Icon(
                name=self.app_name,
                icon=icon_image,
                title=self.app_name,
                menu=menu
            )
            
            # バックグラウンドスレッドで実行
            self._thread = threading.Thread(
                target=self._run_tray,
                daemon=True
            )
            self._thread.start()
            
            self._visible = True
            return True
            
        except Exception:
            return False
    
    def hide(self) -> None:
        """システムトレイアイコンを非表示"""
        try:
            if self._icon:
                self._icon.stop()
            self._visible = False
        except Exception:
            pass
    
    def is_visible(self) -> bool:
        """表示状態を取得"""
        return self._visible
    
    def update_menu(self, menu_items: List[TrayMenuItem]) -> None:
        """メニューを更新"""
        self._menu_items = menu_items[:]
        
        if self._icon and self._visible:
            # アイコンを再作成してメニューを更新
            self.hide()
            self.show()
    
    def add_menu_item(self, item: TrayMenuItem) -> None:
        """メニューアイテムを追加"""
        # 終了メニューの前に挿入
        if self._menu_items and self._menu_items[-1].title == "終了":
            self._menu_items.insert(-1, item)
        else:
            self._menu_items.append(item)
    
    def remove_menu_item(self, title: str) -> bool:
        """メニューアイテムを削除"""
        for i, item in enumerate(self._menu_items):
            if item.title == title:
                del self._menu_items[i]
                return True
        return False
    
    def set_callback(self, event: str, callback: Callable) -> None:
        """イベントコールバックを設定"""
        self._callbacks[event] = callback
    
    def show_notification(self, title: str, message: str, timeout: int = 3) -> None:
        """通知を表示"""
        try:
            if self._icon and self._visible:
                self._icon.notify(message, title)
        except Exception:
            pass
    
    def _create_icon_image(self):
        """トレイアイコン画像を作成"""
        try:
            # 16x16のシンプルなアイコンを作成
            size = 16
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # 青い円を描画
            margin = 2
            draw.ellipse(
                [margin, margin, size - margin, size - margin],
                fill=(74, 144, 226, 255),  # #4A90E2
                outline=(46, 91, 186, 255)  # #2E5BBA
            )
            
            # 中央に小さな白い四角
            center = size // 2
            symbol_size = 3
            draw.rectangle([
                center - symbol_size//2, center - symbol_size//2,
                center + symbol_size//2, center + symbol_size//2
            ], fill=(255, 255, 255, 255))
            
            return image
            
        except Exception:
            # フォールバック: 最小限のダミー画像
            try:
                image = Image.new('RGBA', (16, 16), (74, 144, 226, 255))
                return image
            except Exception:
                # 最終的なフォールバック
                return Image()
    
    def _create_menu(self) -> Menu:
        """トレイメニューを作成"""
        try:
            menu_list = []
            
            for item in self._menu_items:
                if item.separator:
                    menu_list.append(pystray.Menu.SEPARATOR)
                else:
                    menu_list.append(
                        pystray.MenuItem(
                            item.title,
                            item.action,
                            checked=lambda item=item: item.checked,
                            enabled=item.enabled
                        )
                    )
            
            return pystray.Menu(*menu_list)
            
        except Exception:
            # 最小限のメニュー
            return pystray.Menu(
                pystray.MenuItem("設定", self._on_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("終了", self._on_exit)
            )
    
    def _run_tray(self) -> None:
        """トレイアイコンを実行（バックグラウンドスレッド用）"""
        try:
            if self._icon:
                self._icon.run()
        except Exception:
            pass
    
    def _on_settings(self, icon=None, item=None) -> None:
        """設定メニュークリック処理"""
        if 'settings' in self._callbacks:
            try:
                # メインスレッドで実行
                self._schedule_callback('settings')
            except Exception:
                pass
    
    def _on_exit(self, icon=None, item=None) -> None:
        """終了メニューク処理"""
        if 'exit' in self._callbacks:
            try:
                # メインスレッドで実行
                self._schedule_callback('exit')
            except Exception:
                pass
        else:
            # デフォルトの終了処理
            self._default_exit()
    
    def _schedule_callback(self, event: str) -> None:
        """コールバックをメインスレッドにスケジュール"""
        try:
            def run_callback():
                if event in self._callbacks:
                    self._callbacks[event]()
            
            # tkinterのafter()を使用してメインスレッドで実行
            root = tk._default_root
            if root:
                root.after(0, run_callback)
        except Exception:
            # 直接実行をフォールバック
            if event in self._callbacks:
                self._callbacks[event]()
    
    def _default_exit(self) -> None:
        """デフォルトの終了処理"""
        try:
            self.hide()
            # アプリケーション終了
            if hasattr(sys, 'exit'):
                sys.exit(0)
        except Exception:
            pass


class SystemTrayManager:
    """システムトレイマネージャー（高レベルAPI）"""
    
    def __init__(self, app_name: str = "フローティングランチャー"):
        """システムトレイマネージャーの初期化"""
        self.app_name = app_name
        self._tray = None
        self._enabled = True
    
    def initialize(self) -> bool:
        """システムトレイを初期化"""
        if not TRAY_AVAILABLE:
            return False
            
        try:
            self._tray = SystemTray(self.app_name)
            return True
        except Exception:
            return False
    
    def start(self) -> bool:
        """システムトレイを開始"""
        if not self._enabled or not self._tray:
            return False
            
        return self._tray.show()
    
    def stop(self) -> None:
        """システムトレイを停止"""
        if self._tray:
            self._tray.hide()
    
    def is_running(self) -> bool:
        """動作状態を取得"""
        return self._tray and self._tray.is_visible()
    
    def set_callbacks(self, callbacks: Dict[str, Callable]) -> None:
        """コールバックを設定"""
        if self._tray:
            for event, callback in callbacks.items():
                self._tray.set_callback(event, callback)
    
    def add_menu_item(self, title: str, action: Callable = None) -> None:
        """メニューアイテムを追加"""
        if self._tray:
            item = TrayMenuItem(title, action)
            self._tray.add_menu_item(item)
    
    def notify(self, title: str, message: str, timeout: int = 3) -> None:
        """通知を表示"""
        if self._tray:
            self._tray.show_notification(title, message, timeout)
    
    def set_enabled(self, enabled: bool) -> None:
        """システムトレイ機能の有効/無効を設定"""
        self._enabled = enabled
        
        if not enabled and self._tray:
            self.stop()
        elif enabled and self._tray:
            self.start()
    
    def is_available(self) -> bool:
        """システムトレイが利用可能かチェック"""
        return TRAY_AVAILABLE
    
    def get_status(self) -> Dict[str, any]:
        """ステータス情報を取得"""
        return {
            'available': TRAY_AVAILABLE,
            'enabled': self._enabled,
            'running': self.is_running(),
            'app_name': self.app_name
        }