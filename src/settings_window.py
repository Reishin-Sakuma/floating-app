"""
設定画面UI実装
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple, Callable
import os


@dataclass
class SettingsTab:
    """設定タブの基底クラス"""
    name: str
    frame: Optional[tk.Frame] = None
    
    def create_widgets(self, parent: tk.Widget) -> None:
        """ウィジェットを作成する（オーバーライド必須）"""
        raise NotImplementedError
    
    def load_settings(self, config: Dict) -> None:
        """設定値をUIに読み込む（オーバーライド必須）"""
        raise NotImplementedError
    
    def save_settings(self) -> Dict:
        """UIから設定値を取得する（オーバーライド必須）"""
        raise NotImplementedError
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """設定値を検証する（オーバーライド必須）"""
        raise NotImplementedError


class ApplicationTab(SettingsTab):
    """アプリケーション設定タブ"""
    
    def __init__(self, parent=None, config_manager=None):
        super().__init__("アプリケーション")
        self.parent = parent
        self.config_manager = config_manager
        self.app_path_var = None
        self.app_name_var = None
        self.app_args_var = None
        self._initialize_vars()
    
    def _initialize_vars(self):
        """tkinter変数を遅延初期化"""
        try:
            self.app_path_var = tk.StringVar()
            self.app_name_var = tk.StringVar() 
            self.app_args_var = tk.StringVar()
        except RuntimeError:
            # rootウィンドウがない場合は後で初期化
            pass
    
    def create_widgets(self, parent: tk.Widget) -> None:
        """アプリケーション設定のウィジェットを作成"""
        # 変数が初期化されていない場合は初期化
        if self.app_path_var is None:
            self._initialize_vars()
        
        self.frame = ttk.Frame(parent)
        
        # アプリケーションパス
        ttk.Label(self.frame, text="アプリケーションパス:").grid(row=0, column=0, sticky="w", pady=5)
        path_frame = ttk.Frame(self.frame)
        path_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        ttk.Entry(path_frame, textvariable=self.app_path_var, width=50).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame, text="参照", command=self._browse_app_path).pack(side="right", padx=(5, 0))
        
        # アプリケーション名
        ttk.Label(self.frame, text="表示名:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(self.frame, textvariable=self.app_name_var, width=30).grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # 起動引数
        ttk.Label(self.frame, text="起動引数:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(self.frame, textvariable=self.app_args_var, width=50).grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        self.frame.columnconfigure(1, weight=1)
    
    def load_settings(self, config: Dict) -> None:
        """設定値をUIに読み込む"""
        if self.app_path_var is None:
            self._initialize_vars()
            
        if self.app_path_var:
            self.app_path_var.set(config.get('app_path', ''))
            self.app_name_var.set(config.get('app_name', ''))
            self.app_args_var.set(config.get('app_args', ''))
    
    def save_settings(self) -> Dict:
        """UIから設定値を取得"""
        if not self.app_path_var:
            return {}
            
        return {
            'app_path': self.app_path_var.get(),
            'app_name': self.app_name_var.get(),
            'app_args': self.app_args_var.get()
        }
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """設定値を検証"""
        if not self.app_path_var:
            return True, None
            
        app_path = self.app_path_var.get().strip()
        if not app_path:
            return False, "アプリケーションパスが設定されていません。"
        
        if not os.path.exists(app_path):
            return False, f"指定されたパスが存在しません: {app_path}"
        
        if not os.path.isfile(app_path):
            return False, f"指定されたパスはファイルではありません: {app_path}"
        
        # 実行可能ファイルかチェック（Windows）
        _, ext = os.path.splitext(app_path.lower())
        if ext not in ['.exe', '.bat', '.cmd', '.com']:
            return False, f"実行可能ファイルではありません: {app_path}"
        
        return True, None
    
    def _browse_app_path(self) -> None:
        """アプリケーションパス選択ダイアログ"""
        try:
            file_path = filedialog.askopenfilename(
                title="アプリケーションを選択",
                filetypes=[
                    ("実行ファイル", "*.exe"),
                    ("バッチファイル", "*.bat;*.cmd"),
                    ("すべてのファイル", "*.*")
                ]
            )
            if file_path:
                self.app_path_var.set(file_path)
                # ファイル名から表示名を自動設定
                if not self.app_name_var.get():
                    basename = os.path.basename(file_path)
                    name, _ = os.path.splitext(basename)
                    self.app_name_var.set(name)
        except Exception:
            pass
    
    def browse_application(self) -> None:
        """アプリケーション選択（テスト用のパブリックメソッド）"""
        self._browse_app_path()
    
    def validate_application_path(self, path: str) -> Tuple[bool, str]:
        """アプリケーションパスを検証する（テスト用）"""
        try:
            if not path or not path.strip():
                return False, "アプリケーションパスが設定されていません。"
            
            if not os.path.exists(path):
                return False, f"指定されたパスが存在しません: {path}"
            
            if not os.path.isfile(path):
                return False, f"指定されたパスはファイルではありません: {path}"
            
            # 実行可能ファイルかチェック（Windows）
            _, ext = os.path.splitext(path.lower())
            if ext not in ['.exe', '.bat', '.cmd', '.com']:
                return False, f"実行可能ファイルではありません: {path}"
            
            return True, "有効なアプリケーションパスです。"
            
        except Exception as e:
            return False, f"検証中にエラーが発生しました: {str(e)}"
    
    def get_application_info(self, path: str = None) -> Dict:
        """アプリケーション情報を取得"""
        if path:
            # パスが指定された場合はそのファイルの情報を取得
            try:
                if os.path.exists(path) and os.path.isfile(path):
                    basename = os.path.basename(path)
                    name, _ = os.path.splitext(basename)
                    return {
                        'path': path,
                        'name': name,
                        'exists': True,
                        'size': os.path.getsize(path)
                    }
                else:
                    return {
                        'path': path,
                        'exists': False
                    }
            except Exception:
                return {
                    'path': path,
                    'exists': False,
                    'error': True
                }
        
        # パスが指定されていない場合はUI状態から取得
        if not self.app_path_var:
            return {}
            
        return {
            'path': self.app_path_var.get(),
            'name': self.app_name_var.get(),
            'args': self.app_args_var.get()
        }


class AppearanceTab(SettingsTab):
    """外観設定タブ"""
    
    def __init__(self, parent=None, config_manager=None):
        super().__init__("外観")
        self.parent = parent
        self.config_manager = config_manager
        self.icon_size_var = None
        self.icon_x_var = None
        self.icon_y_var = None
        self.opacity_var = None
        self._initialize_vars()
    
    def _initialize_vars(self):
        """tkinter変数を遅延初期化"""
        try:
            self.icon_size_var = tk.IntVar(value=32)
            self.icon_x_var = tk.IntVar(value=100)
            self.icon_y_var = tk.IntVar(value=100)
            self.opacity_var = tk.DoubleVar(value=0.9)
        except RuntimeError:
            # rootウィンドウがない場合は後で初期化
            pass
    
    def create_widgets(self, parent: tk.Widget) -> None:
        """外観設定のウィジェットを作成"""
        # 変数が初期化されていない場合は初期化
        if self.icon_size_var is None:
            self._initialize_vars()
            
        self.frame = ttk.Frame(parent)
        
        # アイコンサイズ
        ttk.Label(self.frame, text="アイコンサイズ:").grid(row=0, column=0, sticky="w", pady=5)
        size_frame = ttk.Frame(self.frame)
        size_frame.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Scale(size_frame, from_=16, to=64, variable=self.icon_size_var, orient="horizontal").pack(side="left")
        ttk.Label(size_frame, textvariable=self.icon_size_var).pack(side="left", padx=(10, 0))
        ttk.Label(size_frame, text="px").pack(side="left")
        
        # アイコン位置
        ttk.Label(self.frame, text="アイコン位置:").grid(row=1, column=0, sticky="w", pady=5)
        pos_frame = ttk.Frame(self.frame)
        pos_frame.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(pos_frame, text="X:").pack(side="left")
        ttk.Entry(pos_frame, textvariable=self.icon_x_var, width=8).pack(side="left", padx=(5, 10))
        ttk.Label(pos_frame, text="Y:").pack(side="left")
        ttk.Entry(pos_frame, textvariable=self.icon_y_var, width=8).pack(side="left", padx=(5, 0))
        
        # 不透明度
        ttk.Label(self.frame, text="不透明度:").grid(row=2, column=0, sticky="w", pady=5)
        opacity_frame = ttk.Frame(self.frame)
        opacity_frame.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Scale(opacity_frame, from_=0.1, to=1.0, variable=self.opacity_var, orient="horizontal").pack(side="left")
        opacity_label = ttk.Label(opacity_frame, text="")
        opacity_label.pack(side="left", padx=(10, 0))
        
        # 不透明度の値を更新するコールバック
        def update_opacity_label(*args):
            opacity_label.config(text=f"{self.opacity_var.get():.1f}")
        
        self.opacity_var.trace_add("write", update_opacity_label)
        update_opacity_label()
    
    def load_settings(self, config: Dict) -> None:
        """設定値をUIに読み込む"""
        if self.icon_size_var is None:
            self._initialize_vars()
            
        if self.icon_size_var:
            self.icon_size_var.set(config.get('icon_size', 32))
            
            icon_pos = config.get('icon_position', {'x': 100, 'y': 100})
            if isinstance(icon_pos, dict):
                self.icon_x_var.set(icon_pos.get('x', 100))
                self.icon_y_var.set(icon_pos.get('y', 100))
            
            self.opacity_var.set(config.get('icon_opacity', 0.9))
    
    def save_settings(self) -> Dict:
        """UIから設定値を取得"""
        if not self.icon_size_var:
            return {}
            
        return {
            'icon_size': self.icon_size_var.get(),
            'icon_position': {
                'x': self.icon_x_var.get(),
                'y': self.icon_y_var.get()
            },
            'icon_opacity': self.opacity_var.get()
        }
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """設定値を検証"""
        if not self.icon_size_var:
            return True, None
            
        size = self.icon_size_var.get()
        if size < 16 or size > 128:
            return False, "アイコンサイズは16-128pxの範囲で指定してください。"
        
        x = self.icon_x_var.get()
        y = self.icon_y_var.get()
        if x < 0 or y < 0:
            return False, "アイコン位置は0以上で指定してください。"
        
        opacity = self.opacity_var.get()
        if opacity < 0.1 or opacity > 1.0:
            return False, "不透明度は0.1-1.0の範囲で指定してください。"
        
        return True, None


class GeneralTab(SettingsTab):
    """一般設定タブ"""
    
    def __init__(self, parent=None, config_manager=None):
        super().__init__("一般")
        self.parent = parent
        self.config_manager = config_manager
        self.auto_start_var = None
        self.show_tray_var = None
        self.drag_enabled_var = None
        self._initialize_vars()
    
    def _initialize_vars(self):
        """tkinter変数を遅延初期化"""
        try:
            self.auto_start_var = tk.BooleanVar(value=False)
            self.show_tray_var = tk.BooleanVar(value=True)
            self.drag_enabled_var = tk.BooleanVar(value=True)
        except RuntimeError:
            # rootウィンドウがない場合は後で初期化
            pass
    
    def create_widgets(self, parent: tk.Widget) -> None:
        """一般設定のウィジェットを作成"""
        # 変数が初期化されていない場合は初期化  
        if self.auto_start_var is None:
            self._initialize_vars()
            
        self.frame = ttk.Frame(parent)
        
        # 自動起動
        ttk.Checkbutton(
            self.frame, 
            text="Windows起動時に自動起動する", 
            variable=self.auto_start_var
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        # システムトレイ表示
        ttk.Checkbutton(
            self.frame, 
            text="システムトレイにアイコンを表示する", 
            variable=self.show_tray_var
        ).grid(row=1, column=0, sticky="w", pady=5)
        
        # ドラッグ移動
        ttk.Checkbutton(
            self.frame, 
            text="アイコンのドラッグ移動を有効にする", 
            variable=self.drag_enabled_var
        ).grid(row=2, column=0, sticky="w", pady=5)
    
    def load_settings(self, config: Dict) -> None:
        """設定値をUIに読み込む"""
        if self.auto_start_var is None:
            self._initialize_vars()
            
        if self.auto_start_var:
            self.auto_start_var.set(config.get('auto_start', False))
            self.show_tray_var.set(config.get('show_tray_icon', True))
            self.drag_enabled_var.set(config.get('drag_enabled', True))
    
    def save_settings(self) -> Dict:
        """UIから設定値を取得"""
        if not self.auto_start_var:
            return {}
            
        return {
            'auto_start': self.auto_start_var.get(),
            'show_tray_icon': self.show_tray_var.get(),
            'drag_enabled': self.drag_enabled_var.get()
        }
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """設定値を検証（一般設定は特に検証不要）"""
        return True, None


class SettingsWindow:
    """設定画面UIクラス"""
    
    def __init__(self, config_manager):
        """設定画面の初期化"""
        self.config_manager = config_manager
        self._window = None
        self._notebook = None
        self._tabs = []
        self._callbacks = {}
        
        # タブを初期化
        self._init_tabs()
    
    def _init_tabs(self) -> None:
        """設定タブを初期化"""
        self._tabs = [
            ApplicationTab(None, self.config_manager),
            AppearanceTab(None, self.config_manager),
            GeneralTab(None, self.config_manager)
        ]
    
    def show(self) -> bool:
        """設定ウィンドウを表示"""
        try:
            if not self._window:
                self._create_window()
            
            if self._window:
                self._window.deiconify()
                self._window.lift()
                self._window.focus_force()
                self.load_settings_to_ui()
                return True
            
        except Exception:
            pass
        
        return False
    
    def hide(self) -> None:
        """設定ウィンドウを非表示"""
        try:
            if self._window:
                self._window.withdraw()
        except Exception:
            pass
    
    def destroy(self) -> None:
        """設定ウィンドウを破棄"""
        try:
            if self._window:
                self._window.destroy()
                self._window = None
        except Exception:
            pass
    
    def apply_settings(self) -> bool:
        """設定を適用"""
        try:
            # 全タブの検証
            for tab in self._tabs:
                valid, error_msg = tab.validate()
                if not valid:
                    messagebox.showerror("設定エラー", error_msg)
                    return False
            
            # 設定を収集
            config = {}
            for tab in self._tabs:
                settings = tab.save_settings()
                config.update(settings)
            
            # 設定を保存
            current_config = self.config_manager.load_config() or {}
            current_config.update(config)
            self.config_manager.save_config(current_config)
            
            # コールバック実行
            if 'apply' in self._callbacks:
                self._callbacks['apply'](config)
            
            return True
            
        except Exception:
            return False
    
    def cancel_settings(self) -> None:
        """設定をキャンセル"""
        try:
            self.load_settings_to_ui()  # 元の設定に戻す
            self.hide()  # ウィンドウを隠す
            if 'cancel' in self._callbacks:
                self._callbacks['cancel']()
        except Exception:
            pass
    
    def reset_to_defaults(self) -> bool:
        """デフォルト設定にリセット"""
        try:
            default_config = self.config_manager.get_default_config()
            for tab in self._tabs:
                tab.load_settings(default_config)
            return True
        except Exception:
            return False
    
    def validate_settings(self) -> Tuple[bool, List[str]]:
        """全設定の検証"""
        errors = []
        for tab in self._tabs:
            try:
                valid, error_msg = tab.validate()
                if not valid and error_msg:
                    errors.append(error_msg)
            except Exception:
                pass
        
        return len(errors) == 0, errors
    
    def get_current_settings(self) -> Dict:
        """現在のUI設定値を取得"""
        try:
            config = {}
            for tab in self._tabs:
                settings = tab.save_settings()
                config.update(settings)
            return config
        except Exception:
            return {}
    
    def load_settings_to_ui(self, config: Dict = None) -> None:
        """設定値をUIに読み込む"""
        try:
            if config is None:
                config = self.config_manager.load_config() or {}
            for tab in self._tabs:
                tab.load_settings(config)
        except Exception:
            pass
    
    def set_callback(self, event: str, callback: Callable) -> None:
        """イベントコールバックを設定"""
        self._callbacks[event] = callback
    
    def _create_window(self) -> None:
        """ウィンドウを作成"""
        try:
            self._window = tk.Toplevel()
            self._window.title("フローティングランチャー設定")
            self._window.geometry("600x400")
            self._window.resizable(True, True)
            
            # モーダルウィンドウ設定
            self._window.transient()
            self._window.grab_set()
            
            # ウィンドウを中央に配置
            self._center_window()
            
            # ノートブックウィジェット作成
            self._create_notebook()
            
            # ボタンエリア作成
            self._create_buttons()
            
            # ウィンドウクローズイベント
            self._window.protocol("WM_DELETE_WINDOW", self.hide)
            
        except Exception:
            self._window = None
    
    def _center_window(self) -> None:
        """ウィンドウを画面中央に配置"""
        try:
            self._window.update_idletasks()
            width = self._window.winfo_width()
            height = self._window.winfo_height()
            screen_width = self._window.winfo_screenwidth()
            screen_height = self._window.winfo_screenheight()
            
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            self._window.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass
    
    def _create_notebook(self) -> None:
        """ノートブックとタブを作成"""
        try:
            self._notebook = ttk.Notebook(self._window)
            self._notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            for tab in self._tabs:
                tab.create_widgets(self._notebook)
                self._notebook.add(tab.frame, text=tab.name)
                
        except Exception:
            pass
    
    def _create_buttons(self) -> None:
        """ボタンエリアを作成"""
        try:
            button_frame = ttk.Frame(self._window)
            button_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # 右寄せのボタン配置
            ttk.Button(
                button_frame, 
                text="デフォルトに戻す", 
                command=self.reset_to_defaults
            ).pack(side="left")
            
            ttk.Button(
                button_frame, 
                text="キャンセル", 
                command=self.cancel_settings
            ).pack(side="right", padx=(5, 0))
            
            ttk.Button(
                button_frame, 
                text="適用", 
                command=self._on_apply
            ).pack(side="right")
            
            ttk.Button(
                button_frame, 
                text="OK", 
                command=self._on_ok
            ).pack(side="right", padx=(0, 5))
            
        except Exception:
            pass
    
    def _on_ok(self) -> None:
        """OKボタンクリック処理"""
        if self.apply_settings():
            self.hide()
    
    def _on_apply(self) -> None:
        """適用ボタンクリック処理"""
        self.apply_settings()