"""
フローティングアイコン描画エンジン
"""
import tkinter as tk
from dataclasses import dataclass
from typing import Optional, Tuple, Callable
import time


@dataclass
class IconStyle:
    """アイコンスタイル設定"""
    size: int = 32
    background_color: str = "#4A90E2"
    border_color: str = "#2E5BBA"
    border_width: int = 2
    corner_radius: int = 8
    shadow_enabled: bool = True
    shadow_color: str = "#000000"
    shadow_offset: Tuple[int, int] = (2, 2)
    opacity: float = 0.9


@dataclass
class DisplayInfo:
    """ディスプレイ情報"""
    width: int
    height: int
    dpi_scale: float
    is_primary: bool
    bounds: Tuple[int, int, int, int]  # (x, y, width, height)


class FloatingIcon:
    """フローティングアイコン描画エンジン"""

    def __init__(self, config_manager):
        """フローティングアイコンの初期化"""
        self.config_manager = config_manager
        self._window = None
        self._canvas = None
        self._visible = False
        self._position = (100, 100)
        self._size = 32
        self._click_callback = None
        self._right_click_callback = None
        self._style = IconStyle()
        
        # インタラクション状態
        self._is_hovered = False
        self._drag_start_pos = None
        self._drag_start_window_pos = None
        self._drag_enabled = True
        self._transparent_enabled = False
        
        # 設定から初期値を読み込み
        config = config_manager.load_config()
        if config and 'icon_position' in config:
            pos = config['icon_position']
            if isinstance(pos, dict) and 'x' in pos and 'y' in pos:
                try:
                    x = int(pos['x']) if isinstance(pos['x'], (int, float, str)) else 100
                    y = int(pos['y']) if isinstance(pos['y'], (int, float, str)) else 100
                    self._position = (max(0, x), max(0, y))
                except (ValueError, TypeError):
                    self._position = (100, 100)
        
        if config and 'icon_size' in config:
            try:
                size = int(config['icon_size']) if isinstance(config['icon_size'], (int, float, str)) else 32
                self._size = max(16, size)
            except (ValueError, TypeError):
                self._size = 32

    def show(self) -> bool:
        """アイコンを表示する"""
        try:
            if not self._window:
                self._create_window()
            if self._window:
                try:
                    self._window.deiconify()
                except AttributeError:
                    # テスト時のモック対応
                    pass
                self._visible = True
                self._update_display()
                return True
        except Exception:
            pass
        return False

    def hide(self) -> bool:
        """アイコンを非表示にする"""
        try:
            if self._window:
                try:
                    self._window.withdraw()
                except AttributeError:
                    # テスト時のモック対応
                    pass
                self._visible = False
                return True
        except Exception:
            pass
        return False

    def update_position(self, x: int, y: int) -> bool:
        """アイコンの位置を更新する"""
        try:
            # 境界チェックで位置を調整
            x, y = self._ensure_position_in_bounds(x, y)
            
            self._position = (x, y)
            
            if self._window and self._visible:
                self._window.geometry(f"{self._size}x{self._size}+{x}+{y}")
            
            return True
        except Exception:
            return False

    def update_size(self, size: int) -> bool:
        """アイコンのサイズを更新する"""
        try:
            if size <= 0:
                return False
            
            self._size = size
            
            if self._window and self._visible:
                x, y = self._position
                self._window.geometry(f"{size}x{size}+{x}+{y}")
                self._update_display()
            
            return True
        except Exception:
            return False

    def set_click_callback(self, callback: Callable) -> None:
        """クリックコールバックを設定する"""
        self._click_callback = callback

    def set_right_click_callback(self, callback: Callable) -> None:
        """右クリックコールバックを設定する"""
        self._right_click_callback = callback

    def is_visible(self) -> bool:
        """表示状態を確認する"""
        return self._visible

    def get_position(self) -> Tuple[int, int]:
        """現在の位置を取得する"""
        return self._position

    def get_size(self) -> int:
        """現在のサイズを取得する"""
        return self._size

    def refresh(self) -> None:
        """アイコンを再描画する"""
        if self._window and self._canvas and self._visible:
            self._update_display()

    def _handle_left_click(self, event) -> None:
        """左クリックイベント処理"""
        if self._click_callback:
            self._click_callback()

    def _handle_right_click(self, event) -> None:
        """右クリックイベント処理"""
        if self._right_click_callback:
            self._right_click_callback()

    def _create_window(self) -> None:
        """ウィンドウを作成する"""
        try:
            self._window = tk.Toplevel()
            
            # ウィンドウの基本設定
            x, y = self._position
            self._window.geometry(f"{self._size}x{self._size}+{x}+{y}")
            self._window.overrideredirect(True)
            self._window.wm_attributes("-topmost", True)
            
            # 透明背景の設定（Windows対応）
            try:
                self._window.wm_attributes("-transparentcolor", "#000001")
                self._transparent_enabled = True
            except tk.TclError:
                self._transparent_enabled = False
            
            # Canvas作成（透明背景対応）
            bg_color = "#000001" if self._transparent_enabled else "#F0F0F0"
            self._canvas = tk.Canvas(
                self._window, 
                width=self._size, 
                height=self._size,
                highlightthickness=0,
                bg=bg_color
            )
            self._canvas.pack(fill=tk.BOTH, expand=True)
            
            # イベントバインディング
            self._setup_event_bindings()
            
        except Exception:
            self._window = None
            self._canvas = None

    def _setup_event_bindings(self) -> None:
        """イベントバインディングの設定"""
        if not self._canvas:
            return
        
        # マウスイベント
        self._canvas.bind("<Button-1>", self._handle_left_click)
        self._canvas.bind("<Button-3>", self._handle_right_click)
        
        # ホバーエフェクト
        self._canvas.bind("<Enter>", self._on_mouse_enter)
        self._canvas.bind("<Leave>", self._on_mouse_leave)
        
        # ドラッグ機能（設定で有効な場合）
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas.bind("<ButtonRelease-1>", self._on_drag_end)

    def _update_display(self) -> None:
        """表示を更新する"""
        if not self._canvas:
            return
        
        try:
            # キャンバスクリア
            self._canvas.delete("all")
            
            # DPIスケーリング適用
            dpi_scale = self._get_dpi_scale()
            effective_size = int(self._size * dpi_scale)
            
            # ドロップシャドウの描画
            if self._style.shadow_enabled:
                self._draw_shadow()
            
            # メインアイコンの描画
            self._draw_main_icon()
            
            # ホバー効果の適用
            if hasattr(self, '_is_hovered') and self._is_hovered:
                self._draw_hover_effect()
                
        except Exception:
            pass

    def _draw_shadow(self) -> None:
        """ドロップシャドウを描画"""
        if not self._canvas or not self._style.shadow_enabled:
            return
        
        try:
            margin = 2
            shadow_offset_x, shadow_offset_y = self._style.shadow_offset
            
            self._canvas.create_oval(
                margin + shadow_offset_x, 
                margin + shadow_offset_y, 
                self._size - margin + shadow_offset_x, 
                self._size - margin + shadow_offset_y,
                fill=self._style.shadow_color,
                outline="",
                stipple="gray50"  # 半透明効果
            )
        except Exception:
            pass

    def _draw_main_icon(self) -> None:
        """メインアイコンを描画"""
        if not self._canvas:
            return
        
        try:
            margin = 2
            
            # 角丸の円形アイコン
            self._canvas.create_oval(
                margin, margin, 
                self._size - margin, self._size - margin,
                fill=self._style.background_color,
                outline=self._style.border_color,
                width=self._style.border_width,
                tags="main_icon"
            )
            
            # 中央にシンプルなアイコンシンボル（フォルダアイコン風）
            self._draw_icon_symbol()
            
        except Exception:
            pass

    def _draw_icon_symbol(self) -> None:
        """アイコンシンボルを描画"""
        if not self._canvas:
            return
        
        try:
            center = self._size // 2
            symbol_size = self._size // 4
            
            # シンプルなフォルダアイコン風の描画
            self._canvas.create_rectangle(
                center - symbol_size, center - symbol_size//2,
                center + symbol_size, center + symbol_size//2,
                fill="white",
                outline=self._style.border_color,
                width=1,
                tags="symbol"
            )
            
        except Exception:
            pass

    def _draw_hover_effect(self) -> None:
        """ホバーエフェクトを描画"""
        if not self._canvas:
            return
        
        try:
            margin = 1
            
            # ホバー時の外枠
            self._canvas.create_oval(
                margin, margin, 
                self._size - margin, self._size - margin,
                fill="",
                outline="#FFD700",  # ゴールド色のハイライト
                width=2,
                tags="hover_effect"
            )
            
        except Exception:
            pass

    def _on_mouse_enter(self, event) -> None:
        """マウスホバー開始"""
        self._is_hovered = True
        self._update_display()

    def _on_mouse_leave(self, event) -> None:
        """マウスホバー終了"""
        self._is_hovered = False
        self._update_display()

    def _on_drag_start(self, event) -> None:
        """ドラッグ開始"""
        if self._drag_enabled:
            # ウィンドウ座標系での初期位置を記録
            self._drag_start_pos = (event.x_root, event.y_root)
            self._drag_start_window_pos = self._position

    def _on_drag(self, event) -> None:
        """ドラッグ中の処理"""
        if not self._drag_enabled or not self._drag_start_pos or not self._drag_start_window_pos:
            return
        
        try:
            # スクリーン座標での移動量を計算
            dx = event.x_root - self._drag_start_pos[0]
            dy = event.y_root - self._drag_start_pos[1]
            
            # 新しいウィンドウ位置を計算
            start_x, start_y = self._drag_start_window_pos
            new_x = start_x + dx
            new_y = start_y + dy
            
            # 境界チェックと位置更新
            new_x, new_y = self._ensure_position_in_bounds(new_x, new_y)
            if self.update_position(new_x, new_y):
                # ドラッグ中は頻繁に保存しない（パフォーマンス対策）
                pass
                
        except Exception:
            pass

    def _on_drag_end(self, event) -> None:
        """ドラッグ終了"""
        if self._drag_start_pos:
            # ドラッグが実際に行われた場合のみ位置を保存
            self._save_position_to_config()
            self._drag_start_pos = None
            self._drag_start_window_pos = None

    def _save_position_to_config(self) -> None:
        """位置を設定に保存"""
        try:
            config = self.config_manager.load_config()
            if not config:
                config = {}
            
            config['icon_position'] = {
                'x': self._position[0],
                'y': self._position[1]
            }
            
            self.config_manager.save_config(config)
        except Exception:
            pass

    def set_drag_enabled(self, enabled: bool) -> None:
        """ドラッグ機能の有効/無効を設定"""
        self._drag_enabled = enabled

    def is_drag_enabled(self) -> bool:
        """ドラッグ機能の有効状態を取得"""
        return self._drag_enabled

    def _get_display_info(self) -> DisplayInfo:
        """ディスプレイ情報を取得する"""
        try:
            # 基本的なディスプレイ情報を返す
            root = tk.Tk()
            root.withdraw()
            
            # 仮想スクリーン全体のサイズ
            width = root.winfo_vrootwidth() if hasattr(root, 'winfo_vrootwidth') else root.winfo_screenwidth()
            height = root.winfo_vrootheight() if hasattr(root, 'winfo_vrootheight') else root.winfo_screenheight()
            
            # プライマリディスプレイのサイズ
            primary_width = root.winfo_screenwidth()
            primary_height = root.winfo_screenheight()
            
            # DPI情報
            dpi_scale = self._get_dpi_scale()
            
            root.destroy()
            
            return DisplayInfo(
                width=width,
                height=height,
                dpi_scale=dpi_scale,
                is_primary=True,
                bounds=(0, 0, primary_width, primary_height)
            )
        except Exception:
            return DisplayInfo(
                width=1920,
                height=1080,
                dpi_scale=1.0,
                is_primary=True,
                bounds=(0, 0, 1920, 1080)
            )

    def _get_monitor_bounds(self) -> list:
        """各モニターの境界を取得（将来の拡張用）"""
        try:
            # 現在は基本情報のみ返す（将来的にはWin32 API使用を想定）
            display_info = self._get_display_info()
            return [display_info.bounds]
        except Exception:
            return [(0, 0, 1920, 1080)]

    def _ensure_position_in_bounds(self, x: int, y: int) -> Tuple[int, int]:
        """位置がモニター範囲内に収まるよう調整"""
        try:
            display_info = self._get_display_info()
            
            # 最小値での制限
            x = max(0, x)
            y = max(0, y)
            
            # 最大値での制限（アイコンサイズを考慮）
            max_x = display_info.width - self._size
            max_y = display_info.height - self._size
            
            x = min(max_x, x)
            y = min(max_y, y)
            
            return (x, y)
            
        except Exception:
            # エラー時はそのまま返す
            return (max(0, x), max(0, y))

    def _get_dpi_scale(self) -> float:
        """DPIスケーリングを取得する"""
        try:
            root = tk.Tk()
            root.withdraw()
            
            # DPI計算 (96 DPIが基準)
            dpi = root.winfo_fpixels('1i')
            scale = dpi / 96.0
            
            root.destroy()
            
            return scale
        except Exception:
            return 1.0