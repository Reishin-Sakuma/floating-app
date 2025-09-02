"""
エラーハンドリング強化機能
"""
import sys
import traceback
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import tkinter as tk
from tkinter import messagebox


class ErrorLevel(Enum):
    """エラーレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """エラーカテゴリ"""
    SYSTEM = "SYSTEM"
    FILE_IO = "FILE_IO"
    NETWORK = "NETWORK"
    UI = "UI"
    CONFIG = "CONFIG"
    APPLICATION = "APPLICATION"
    PERMISSION = "PERMISSION"
    RESOURCE = "RESOURCE"


@dataclass
class ErrorInfo:
    """エラー情報"""
    level: ErrorLevel
    category: ErrorCategory
    message: str
    details: Optional[str] = None
    exception: Optional[Exception] = None
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    suggestion: Optional[str] = None
    recovery_action: Optional[str] = None


class ErrorLogger:
    """エラーログ管理クラス"""
    
    def __init__(self, log_dir: str = None, app_name: str = "FloatingLauncher"):
        """エラーログ管理の初期化"""
        self.app_name = app_name
        self._setup_log_directory(log_dir)
        self._setup_logger()
        self._error_history = []
        self._max_history = 1000
    
    def _setup_log_directory(self, log_dir: Optional[str]) -> None:
        """ログディレクトリの設定"""
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            # デフォルトログディレクトリ
            if os.name == 'nt':  # Windows
                self.log_dir = Path.home() / "AppData" / "Local" / self.app_name / "logs"
            else:  # Unix系
                self.log_dir = Path.home() / ".local" / "share" / self.app_name / "logs"
        
        # ディレクトリ作成
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # ログディレクトリ作成失敗時は一時ディレクトリを使用
            import tempfile
            self.log_dir = Path(tempfile.gettempdir()) / f"{self.app_name}_logs"
            self.log_dir.mkdir(exist_ok=True)
    
    def _setup_logger(self) -> None:
        """ログの設定"""
        try:
            # ログファイル名（日付付き）
            log_filename = f"{self.app_name}_{datetime.now().strftime('%Y%m%d')}.log"
            log_file = self.log_dir / log_filename
            
            # ロガー設定
            self.logger = logging.getLogger(f"{self.app_name}_error_handler")
            self.logger.setLevel(logging.DEBUG)
            
            # 既存のハンドラをクリア
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # ファイルハンドラ
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # コンソールハンドラ（デバッグ時のみ）
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # フォーマット設定
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
            # 初期化ログ
            self.logger.info(f"{self.app_name} エラーハンドラー初期化完了")
            
        except Exception:
            # ログ設定に失敗した場合はデフォルトロガー
            self.logger = logging.getLogger(__name__)
    
    def log_error(self, error_info: ErrorInfo) -> None:
        """エラーをログに記録"""
        try:
            # エラー履歴に追加
            self._error_history.append(error_info)
            if len(self._error_history) > self._max_history:
                self._error_history.pop(0)
            
            # ログメッセージ作成
            log_message = self._format_error_message(error_info)
            
            # レベル別ログ出力
            if error_info.level == ErrorLevel.DEBUG:
                self.logger.debug(log_message)
            elif error_info.level == ErrorLevel.INFO:
                self.logger.info(log_message)
            elif error_info.level == ErrorLevel.WARNING:
                self.logger.warning(log_message)
            elif error_info.level == ErrorLevel.ERROR:
                self.logger.error(log_message)
            elif error_info.level == ErrorLevel.CRITICAL:
                self.logger.critical(log_message)
                
        except Exception:
            # ログ出力に失敗した場合はコンソールに出力
            print(f"ERROR: ログ出力失敗 - {error_info.message}")
    
    def _format_error_message(self, error_info: ErrorInfo) -> str:
        """エラーメッセージのフォーマット"""
        parts = [
            f"[{error_info.category.value}] {error_info.message}"
        ]
        
        if error_info.details:
            parts.append(f"詳細: {error_info.details}")
        
        if error_info.context:
            context_str = ", ".join(f"{k}={v}" for k, v in error_info.context.items())
            parts.append(f"コンテキスト: {context_str}")
        
        if error_info.exception:
            parts.append(f"例外: {str(error_info.exception)}")
            if hasattr(error_info.exception, '__traceback__') and error_info.exception.__traceback__:
                tb_lines = traceback.format_exception(
                    type(error_info.exception),
                    error_info.exception,
                    error_info.exception.__traceback__
                )
                parts.append("トレースバック:")
                parts.extend(line.rstrip() for line in tb_lines)
        
        return "\n".join(parts)
    
    def get_error_history(self, limit: Optional[int] = None) -> List[ErrorInfo]:
        """エラー履歴を取得"""
        if limit:
            return self._error_history[-limit:]
        return self._error_history.copy()
    
    def clear_history(self) -> None:
        """エラー履歴をクリア"""
        self._error_history.clear()
    
    def get_log_files(self) -> List[Path]:
        """ログファイル一覧を取得"""
        try:
            pattern = f"{self.app_name}_*.log"
            return list(self.log_dir.glob(pattern))
        except Exception:
            return []


class ErrorRecovery:
    """エラー回復処理クラス"""
    
    def __init__(self):
        """エラー回復処理の初期化"""
        self._recovery_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self._recovery_attempts: Dict[str, int] = {}
        self._max_recovery_attempts = 3
    
    def register_handler(self, category: ErrorCategory, handler: Callable[[ErrorInfo], bool]) -> None:
        """回復処理ハンドラーを登録"""
        if category not in self._recovery_handlers:
            self._recovery_handlers[category] = []
        self._recovery_handlers[category].append(handler)
    
    def attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """エラー回復を試行"""
        try:
            # 回復試行回数をチェック
            error_key = f"{error_info.category.value}:{error_info.message}"
            attempts = self._recovery_attempts.get(error_key, 0)
            
            if attempts >= self._max_recovery_attempts:
                return False
            
            # 回復試行回数を増加
            self._recovery_attempts[error_key] = attempts + 1
            
            # カテゴリ別回復処理を実行
            handlers = self._recovery_handlers.get(error_info.category, [])
            
            for handler in handlers:
                try:
                    if handler(error_info):
                        # 回復成功時は試行回数をリセット
                        self._recovery_attempts[error_key] = 0
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def reset_recovery_attempts(self, category: Optional[ErrorCategory] = None) -> None:
        """回復試行回数をリセット"""
        if category:
            # 特定カテゴリのみリセット
            keys_to_reset = [k for k in self._recovery_attempts.keys() if k.startswith(category.value)]
            for key in keys_to_reset:
                del self._recovery_attempts[key]
        else:
            # 全てリセット
            self._recovery_attempts.clear()


class UserNotification:
    """ユーザー通知クラス"""
    
    def __init__(self, parent_window: Optional[tk.Tk] = None):
        """ユーザー通知の初期化"""
        self.parent_window = parent_window
        self._notification_history = []
        self._max_history = 100
    
    def show_error_dialog(self, error_info: ErrorInfo, show_details: bool = False) -> bool:
        """エラーダイアログを表示"""
        try:
            title = self._get_dialog_title(error_info.level)
            message = self._format_user_message(error_info)
            
            if show_details and error_info.details:
                message += f"\n\n詳細:\n{error_info.details}"
            
            if error_info.suggestion:
                message += f"\n\n推奨対応:\n{error_info.suggestion}"
            
            # レベル別ダイアログ表示
            if error_info.level in [ErrorLevel.ERROR, ErrorLevel.CRITICAL]:
                messagebox.showerror(title, message, parent=self.parent_window)
            elif error_info.level == ErrorLevel.WARNING:
                messagebox.showwarning(title, message, parent=self.parent_window)
            else:
                messagebox.showinfo(title, message, parent=self.parent_window)
            
            # 通知履歴に追加
            self._add_to_history(error_info)
            
            return True
            
        except Exception:
            return False
    
    def show_recovery_dialog(self, error_info: ErrorInfo) -> bool:
        """回復オプションダイアログを表示"""
        try:
            title = "エラー回復"
            message = f"エラーが発生しました: {error_info.message}"
            
            if error_info.recovery_action:
                message += f"\n\n自動回復を試行しますか？\n{error_info.recovery_action}"
                
                result = messagebox.askyesno(title, message, parent=self.parent_window)
                return result
            else:
                message += "\n\n続行しますか？"
                result = messagebox.askokcancel(title, message, parent=self.parent_window)
                return result
                
        except Exception:
            return False
    
    def _get_dialog_title(self, level: ErrorLevel) -> str:
        """ダイアログタイトルを取得"""
        titles = {
            ErrorLevel.DEBUG: "デバッグ情報",
            ErrorLevel.INFO: "情報",
            ErrorLevel.WARNING: "警告",
            ErrorLevel.ERROR: "エラー",
            ErrorLevel.CRITICAL: "重大なエラー"
        }
        return titles.get(level, "通知")
    
    def _format_user_message(self, error_info: ErrorInfo) -> str:
        """ユーザー向けメッセージをフォーマット"""
        # ユーザーフレンドリーなメッセージに変換
        user_messages = {
            "Permission denied": "アクセス権限がありません。管理者として実行してください。",
            "File not found": "ファイルが見つかりません。パスを確認してください。",
            "Connection refused": "接続が拒否されました。ネットワーク設定を確認してください。",
            "Memory error": "メモリ不足です。他のアプリケーションを終了してください。"
        }
        
        message = error_info.message
        for key, user_message in user_messages.items():
            if key.lower() in message.lower():
                message = user_message
                break
        
        return message
    
    def _add_to_history(self, error_info: ErrorInfo) -> None:
        """通知履歴に追加"""
        self._notification_history.append(error_info)
        if len(self._notification_history) > self._max_history:
            self._notification_history.pop(0)
    
    def get_notification_history(self) -> List[ErrorInfo]:
        """通知履歴を取得"""
        return self._notification_history.copy()


class GlobalErrorHandler:
    """グローバルエラーハンドラー"""
    
    def __init__(self, app_name: str = "FloatingLauncher", parent_window: Optional[tk.Tk] = None):
        """グローバルエラーハンドラーの初期化"""
        self.app_name = app_name
        self.logger = ErrorLogger(app_name=app_name)
        self.recovery = ErrorRecovery()
        self.notification = UserNotification(parent_window)
        
        # デフォルト回復ハンドラーを登録
        self._register_default_recovery_handlers()
        
        # システムレベルのエラーハンドラーを設定
        self._setup_system_error_handlers()
    
    def handle_error(self, 
                    error: Exception, 
                    level: ErrorLevel = ErrorLevel.ERROR,
                    category: ErrorCategory = ErrorCategory.APPLICATION,
                    context: Dict[str, Any] = None,
                    show_dialog: bool = True,
                    attempt_recovery: bool = True) -> bool:
        """エラーを統合処理"""
        try:
            # エラー情報を作成
            error_info = self._create_error_info(error, level, category, context)
            
            # ログに記録
            self.logger.log_error(error_info)
            
            # 回復を試行
            recovery_success = False
            if attempt_recovery:
                recovery_success = self.recovery.attempt_recovery(error_info)
                if recovery_success:
                    # 回復成功をログ
                    recovery_info = ErrorInfo(
                        level=ErrorLevel.INFO,
                        category=category,
                        message=f"エラー回復成功: {error_info.message}"
                    )
                    self.logger.log_error(recovery_info)
            
            # ユーザー通知
            if show_dialog and not recovery_success:
                if level in [ErrorLevel.ERROR, ErrorLevel.CRITICAL]:
                    self.notification.show_error_dialog(error_info)
                elif level == ErrorLevel.WARNING:
                    self.notification.show_error_dialog(error_info)
            
            return recovery_success
            
        except Exception:
            # エラーハンドリング自体でエラーが発生した場合の最後の手段
            try:
                print(f"CRITICAL: エラーハンドリング失敗 - {str(error)}")
                messagebox.showerror("重大なエラー", "システムエラーが発生しました")
            except Exception:
                pass
            return False
    
    def _create_error_info(self, 
                          error: Exception, 
                          level: ErrorLevel, 
                          category: ErrorCategory, 
                          context: Dict[str, Any]) -> ErrorInfo:
        """エラー情報を作成"""
        # 推奨対応とリカバリアクションを設定
        suggestion = self._get_error_suggestion(error, category)
        recovery_action = self._get_recovery_action(error, category)
        
        return ErrorInfo(
            level=level,
            category=category,
            message=str(error),
            exception=error,
            context=context or {},
            suggestion=suggestion,
            recovery_action=recovery_action
        )
    
    def _get_error_suggestion(self, error: Exception, category: ErrorCategory) -> Optional[str]:
        """エラー別の推奨対応を取得"""
        suggestions = {
            ErrorCategory.FILE_IO: "ファイルのアクセス権限とパスを確認してください",
            ErrorCategory.PERMISSION: "管理者権限で実行してください",
            ErrorCategory.NETWORK: "ネットワーク接続を確認してください",
            ErrorCategory.CONFIG: "設定ファイルを確認または初期化してください",
            ErrorCategory.RESOURCE: "使用可能なメモリとディスク容量を確認してください"
        }
        return suggestions.get(category)
    
    def _get_recovery_action(self, error: Exception, category: ErrorCategory) -> Optional[str]:
        """エラー別の回復アクションを取得"""
        actions = {
            ErrorCategory.CONFIG: "設定をデフォルト値にリセット",
            ErrorCategory.FILE_IO: "ファイルの再作成を試行",
            ErrorCategory.RESOURCE: "一時ファイルのクリーンアップ"
        }
        return actions.get(category)
    
    def _register_default_recovery_handlers(self) -> None:
        """デフォルト回復ハンドラーを登録"""
        # 設定ファイル関連の回復
        self.recovery.register_handler(ErrorCategory.CONFIG, self._recover_config_error)
        
        # ファイルI/O関連の回復
        self.recovery.register_handler(ErrorCategory.FILE_IO, self._recover_file_io_error)
        
        # リソース関連の回復
        self.recovery.register_handler(ErrorCategory.RESOURCE, self._recover_resource_error)
    
    def _recover_config_error(self, error_info: ErrorInfo) -> bool:
        """設定エラーの回復"""
        try:
            # 設定ファイルの再作成など
            return True  # 実際の回復処理を実装
        except Exception:
            return False
    
    def _recover_file_io_error(self, error_info: ErrorInfo) -> bool:
        """ファイルI/Oエラーの回復"""
        try:
            # ディレクトリ作成など
            return False  # 実装に応じて修正
        except Exception:
            return False
    
    def _recover_resource_error(self, error_info: ErrorInfo) -> bool:
        """リソースエラーの回復"""
        try:
            # 一時ファイルクリーンアップなど
            return False  # 実装に応じて修正
        except Exception:
            return False
    
    def _setup_system_error_handlers(self) -> None:
        """システムレベルのエラーハンドラーを設定"""
        # 未処理例外のキャッチ
        sys.excepthook = self._handle_uncaught_exception
        
        # スレッド例外のキャッチ（Python 3.8+）
        if hasattr(threading, 'excepthook'):
            import threading
            threading.excepthook = self._handle_thread_exception
    
    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """未処理例外のハンドル"""
        if issubclass(exc_type, KeyboardInterrupt):
            # KeyboardInterruptは通常処理
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # その他の例外はエラーハンドリング
        self.handle_error(
            exc_value,
            ErrorLevel.CRITICAL,
            ErrorCategory.SYSTEM,
            {"type": exc_type.__name__}
        )
    
    def _handle_thread_exception(self, args):
        """スレッド例外のハンドル"""
        self.handle_error(
            args.exc_value,
            ErrorLevel.ERROR,
            ErrorCategory.SYSTEM,
            {"thread": args.thread.name if args.thread else "unknown"}
        )