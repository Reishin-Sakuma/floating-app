"""
エラーハンドリング強化機能 テストケース
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock
import threading

import pytest

from src.error_handler import (
    ErrorLevel, ErrorCategory, ErrorInfo, ErrorLogger, 
    ErrorRecovery, UserNotification, GlobalErrorHandler
)


class TestErrorInfo:
    """ErrorInfo データクラスのテストケース"""

    def test_error_info_creation(self):
        """ErrorInfoが正常に作成される"""
        exception = ValueError("test error")
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.APPLICATION,
            message="テストエラー",
            details="詳細情報",
            exception=exception,
            context={"key": "value"},
            suggestion="推奨対応",
            recovery_action="回復アクション"
        )
        
        assert error_info.level == ErrorLevel.ERROR
        assert error_info.category == ErrorCategory.APPLICATION
        assert error_info.message == "テストエラー"
        assert error_info.details == "詳細情報"
        assert error_info.exception == exception
        assert error_info.context == {"key": "value"}
        assert error_info.suggestion == "推奨対応"
        assert error_info.recovery_action == "回復アクション"
        assert isinstance(error_info.timestamp, datetime)

    def test_error_info_defaults(self):
        """ErrorInfoのデフォルト値が正しい"""
        error_info = ErrorInfo(
            level=ErrorLevel.INFO,
            category=ErrorCategory.SYSTEM,
            message="テスト"
        )
        
        assert error_info.details is None
        assert error_info.exception is None
        assert error_info.context == {}
        assert error_info.suggestion is None
        assert error_info.recovery_action is None


class TestErrorLogger:
    """ErrorLogger クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_error_logger_initialization(self):
        """ErrorLoggerが正常に初期化される"""
        logger = ErrorLogger(self.temp_dir, "TestApp")
        
        assert logger is not None
        assert logger.app_name == "TestApp"
        assert logger.log_dir == Path(self.temp_dir)
        assert hasattr(logger, 'log_error')
        assert hasattr(logger, 'get_error_history')
        assert hasattr(logger, 'clear_history')
        assert hasattr(logger, 'get_log_files')

    def test_log_error_basic(self):
        """基本的なエラーログが正常に記録される"""
        logger = ErrorLogger(self.temp_dir, "TestApp")
        
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.APPLICATION,
            message="テストエラー"
        )
        
        logger.log_error(error_info)
        
        # エラー履歴に追加されることを確認
        history = logger.get_error_history()
        assert len(history) == 1
        assert history[0].message == "テストエラー"

    def test_log_error_with_exception(self):
        """例外付きエラーログが正常に記録される"""
        logger = ErrorLogger(self.temp_dir, "TestApp")
        
        exception = ValueError("test exception")
        error_info = ErrorInfo(
            level=ErrorLevel.CRITICAL,
            category=ErrorCategory.SYSTEM,
            message="例外エラー",
            exception=exception
        )
        
        logger.log_error(error_info)
        
        history = logger.get_error_history()
        assert len(history) == 1
        assert history[0].exception == exception

    def test_error_history_limit(self):
        """エラー履歴の上限が正しく動作する"""
        logger = ErrorLogger(self.temp_dir, "TestApp")
        logger._max_history = 3
        
        # 4つのエラーをログ
        for i in range(4):
            error_info = ErrorInfo(
                level=ErrorLevel.INFO,
                category=ErrorCategory.APPLICATION,
                message=f"エラー{i}"
            )
            logger.log_error(error_info)
        
        history = logger.get_error_history()
        assert len(history) == 3  # 上限で制限される
        assert history[0].message == "エラー1"  # 最初のエラーは削除される

    def test_clear_history(self):
        """エラー履歴のクリアが正常に動作する"""
        logger = ErrorLogger(self.temp_dir, "TestApp")
        
        error_info = ErrorInfo(
            level=ErrorLevel.WARNING,
            category=ErrorCategory.CONFIG,
            message="テスト警告"
        )
        logger.log_error(error_info)
        
        assert len(logger.get_error_history()) == 1
        
        logger.clear_history()
        assert len(logger.get_error_history()) == 0

    def test_get_log_files(self):
        """ログファイル一覧の取得が正常に動作する"""
        logger = ErrorLogger(self.temp_dir, "TestApp")
        
        # ダミーログファイル作成
        log_file = logger.log_dir / "TestApp_20240101.log"
        log_file.write_text("test log")
        
        log_files = logger.get_log_files()
        assert len(log_files) >= 1
        assert any("TestApp" in str(f) for f in log_files)

    @patch('src.error_handler.Path.home')
    @patch('src.error_handler.os.name', 'nt')
    def test_default_log_directory_windows(self, mock_home):
        """Windows環境でのデフォルトログディレクトリ"""
        mock_home.return_value = Path("C:/Users/Test")
        
        logger = ErrorLogger(None, "TestApp")
        expected = Path("C:/Users/Test/AppData/Local/TestApp/logs")
        assert logger.log_dir == expected

    @patch('src.error_handler.Path.home')
    @patch('src.error_handler.os.name', 'posix')
    def test_default_log_directory_unix(self, mock_home):
        """Unix環境でのデフォルトログディレクトリ"""
        mock_home.return_value = Path("/home/test")
        
        logger = ErrorLogger(None, "TestApp")
        expected = Path("/home/test/.local/share/TestApp/logs")
        assert logger.log_dir == expected


class TestErrorRecovery:
    """ErrorRecovery クラスのテストケース"""

    def test_error_recovery_initialization(self):
        """ErrorRecoveryが正常に初期化される"""
        recovery = ErrorRecovery()
        
        assert recovery is not None
        assert hasattr(recovery, 'register_handler')
        assert hasattr(recovery, 'attempt_recovery')
        assert hasattr(recovery, 'reset_recovery_attempts')

    def test_register_handler(self):
        """回復ハンドラーの登録が正常に動作する"""
        recovery = ErrorRecovery()
        
        def test_handler(error_info):
            return True
        
        recovery.register_handler(ErrorCategory.CONFIG, test_handler)
        
        # ハンドラーが登録されることを確認
        assert ErrorCategory.CONFIG in recovery._recovery_handlers
        assert len(recovery._recovery_handlers[ErrorCategory.CONFIG]) == 1

    def test_attempt_recovery_success(self):
        """回復処理が成功する場合のテスト"""
        recovery = ErrorRecovery()
        
        def success_handler(error_info):
            return True  # 回復成功
        
        recovery.register_handler(ErrorCategory.FILE_IO, success_handler)
        
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_IO,
            message="ファイルエラー"
        )
        
        result = recovery.attempt_recovery(error_info)
        assert result is True

    def test_attempt_recovery_failure(self):
        """回復処理が失敗する場合のテスト"""
        recovery = ErrorRecovery()
        
        def failure_handler(error_info):
            return False  # 回復失敗
        
        recovery.register_handler(ErrorCategory.NETWORK, failure_handler)
        
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.NETWORK,
            message="ネットワークエラー"
        )
        
        result = recovery.attempt_recovery(error_info)
        assert result is False

    def test_recovery_attempt_limit(self):
        """回復試行回数の上限が正しく動作する"""
        recovery = ErrorRecovery()
        recovery._max_recovery_attempts = 2
        
        def failure_handler(error_info):
            return False  # 常に失敗
        
        recovery.register_handler(ErrorCategory.APPLICATION, failure_handler)
        
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.APPLICATION,
            message="同じエラー"
        )
        
        # 2回試行
        result1 = recovery.attempt_recovery(error_info)
        result2 = recovery.attempt_recovery(error_info)
        
        # 3回目は試行されない
        result3 = recovery.attempt_recovery(error_info)
        
        assert result1 is False
        assert result2 is False
        assert result3 is False

    def test_reset_recovery_attempts(self):
        """回復試行回数のリセットが正常に動作する"""
        recovery = ErrorRecovery()
        
        def failure_handler(error_info):
            return False
        
        recovery.register_handler(ErrorCategory.SYSTEM, failure_handler)
        
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.SYSTEM,
            message="システムエラー"
        )
        
        # 試行回数を増加
        recovery.attempt_recovery(error_info)
        recovery.attempt_recovery(error_info)
        
        # リセット
        recovery.reset_recovery_attempts(ErrorCategory.SYSTEM)
        
        # 再度試行可能になることを確認
        result = recovery.attempt_recovery(error_info)
        assert result is False  # ハンドラーは失敗するが、試行は実行される


class TestUserNotification:
    """UserNotification クラスのテストケース"""

    @patch('src.error_handler.messagebox')
    def test_show_error_dialog_error(self, mock_messagebox):
        """エラーダイアログの表示（ERROR）"""
        notification = UserNotification()
        
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.APPLICATION,
            message="テストエラー"
        )
        
        result = notification.show_error_dialog(error_info)
        
        assert result is True
        mock_messagebox.showerror.assert_called_once()

    @patch('src.error_handler.messagebox')
    def test_show_error_dialog_warning(self, mock_messagebox):
        """エラーダイアログの表示（WARNING）"""
        notification = UserNotification()
        
        error_info = ErrorInfo(
            level=ErrorLevel.WARNING,
            category=ErrorCategory.CONFIG,
            message="設定警告"
        )
        
        result = notification.show_error_dialog(error_info)
        
        assert result is True
        mock_messagebox.showwarning.assert_called_once()

    @patch('src.error_handler.messagebox')
    def test_show_error_dialog_info(self, mock_messagebox):
        """エラーダイアログの表示（INFO）"""
        notification = UserNotification()
        
        error_info = ErrorInfo(
            level=ErrorLevel.INFO,
            category=ErrorCategory.SYSTEM,
            message="情報メッセージ"
        )
        
        result = notification.show_error_dialog(error_info)
        
        assert result is True
        mock_messagebox.showinfo.assert_called_once()

    @patch('src.error_handler.messagebox')
    def test_show_recovery_dialog_with_action(self, mock_messagebox):
        """回復アクション付きダイアログの表示"""
        mock_messagebox.askyesno.return_value = True
        
        notification = UserNotification()
        
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_IO,
            message="ファイルエラー",
            recovery_action="ファイルを再作成"
        )
        
        result = notification.show_recovery_dialog(error_info)
        
        assert result is True
        mock_messagebox.askyesno.assert_called_once()

    @patch('src.error_handler.messagebox')
    def test_show_recovery_dialog_without_action(self, mock_messagebox):
        """回復アクションなしダイアログの表示"""
        mock_messagebox.askokcancel.return_value = False
        
        notification = UserNotification()
        
        error_info = ErrorInfo(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.PERMISSION,
            message="権限エラー"
        )
        
        result = notification.show_recovery_dialog(error_info)
        
        assert result is False
        mock_messagebox.askokcancel.assert_called_once()

    def test_notification_history(self):
        """通知履歴の管理が正常に動作する"""
        notification = UserNotification()
        
        # 初期状態は空
        assert len(notification.get_notification_history()) == 0
        
        # ダイアログ表示で履歴に追加
        with patch('src.error_handler.messagebox'):
            error_info = ErrorInfo(
                level=ErrorLevel.INFO,
                category=ErrorCategory.APPLICATION,
                message="テスト通知"
            )
            notification.show_error_dialog(error_info)
        
        # 履歴に追加されることを確認
        history = notification.get_notification_history()
        assert len(history) == 1
        assert history[0].message == "テスト通知"


class TestGlobalErrorHandler:
    """GlobalErrorHandler クラスのテストケース"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.error_handler.ErrorLogger')
    @patch('src.error_handler.ErrorRecovery')
    @patch('src.error_handler.UserNotification')
    def test_global_error_handler_initialization(self, mock_notification, mock_recovery, mock_logger):
        """GlobalErrorHandlerが正常に初期化される"""
        handler = GlobalErrorHandler("TestApp")
        
        assert handler is not None
        assert handler.app_name == "TestApp"
        assert hasattr(handler, 'handle_error')
        mock_logger.assert_called_once()
        mock_recovery.assert_called_once()
        mock_notification.assert_called_once()

    @patch('src.error_handler.messagebox')
    def test_handle_error_basic(self, mock_messagebox):
        """基本的なエラー処理が正常に動作する"""
        with patch('src.error_handler.ErrorLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            
            handler = GlobalErrorHandler("TestApp")
            
            exception = ValueError("test error")
            result = handler.handle_error(
                exception,
                ErrorLevel.ERROR,
                ErrorCategory.APPLICATION
            )
            
            # ログが記録されることを確認
            mock_logger.log_error.assert_called_once()
            
            # 結果を確認（回復は実装によるが、処理は完了）
            assert isinstance(result, bool)

    def test_create_error_info(self):
        """エラー情報作成が正常に動作する"""
        handler = GlobalErrorHandler("TestApp")
        
        exception = RuntimeError("runtime error")
        context = {"module": "test", "line": 123}
        
        error_info = handler._create_error_info(
            exception,
            ErrorLevel.CRITICAL,
            ErrorCategory.SYSTEM,
            context
        )
        
        assert error_info.level == ErrorLevel.CRITICAL
        assert error_info.category == ErrorCategory.SYSTEM
        assert error_info.message == "runtime error"
        assert error_info.exception == exception
        assert error_info.context == context

    def test_get_error_suggestion(self):
        """エラー別推奨対応の取得が正常に動作する"""
        handler = GlobalErrorHandler("TestApp")
        
        # ファイルI/Oエラーの推奨対応
        suggestion = handler._get_error_suggestion(
            FileNotFoundError("test"),
            ErrorCategory.FILE_IO
        )
        assert suggestion is not None
        assert "ファイル" in suggestion
        
        # 不明なカテゴリ
        suggestion = handler._get_error_suggestion(
            Exception("test"),
            ErrorCategory.NETWORK
        )
        assert suggestion is not None

    def test_get_recovery_action(self):
        """エラー別回復アクションの取得が正常に動作する"""
        handler = GlobalErrorHandler("TestApp")
        
        # 設定エラーの回復アクション
        action = handler._get_recovery_action(
            Exception("config error"),
            ErrorCategory.CONFIG
        )
        assert action is not None
        assert "リセット" in action

    @patch('src.error_handler.sys')
    def test_setup_system_error_handlers(self, mock_sys):
        """システムエラーハンドラーの設定が正常に動作する"""
        handler = GlobalErrorHandler("TestApp")
        
        # sys.excepthookが設定されることを確認
        assert mock_sys.excepthook == handler._handle_uncaught_exception

    def test_handle_uncaught_exception_keyboard_interrupt(self):
        """KeyboardInterruptの処理が正常に動作する"""
        with patch('src.error_handler.sys.__excepthook__') as mock_excepthook:
            handler = GlobalErrorHandler("TestApp")
            
            # KeyboardInterruptは通常処理
            handler._handle_uncaught_exception(
                KeyboardInterrupt, 
                KeyboardInterrupt("test"), 
                None
            )
            
            mock_excepthook.assert_called_once()

    @patch('src.error_handler.messagebox')
    def test_handle_uncaught_exception_other(self, mock_messagebox):
        """その他の未処理例外の処理が正常に動作する"""
        with patch('src.error_handler.ErrorLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            
            handler = GlobalErrorHandler("TestApp")
            
            # その他の例外はエラーハンドリング
            exception = RuntimeError("uncaught error")
            handler._handle_uncaught_exception(
                RuntimeError,
                exception,
                None
            )
            
            mock_logger.log_error.assert_called_once()


class TestErrorHandlerIntegration:
    """エラーハンドラー統合テスト"""

    def setup_method(self):
        """各テストメソッドの実行前に呼ばれるセットアップ"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テストメソッドの実行後に呼ばれるクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.error_handler.messagebox')
    def test_end_to_end_error_handling(self, mock_messagebox):
        """エンドツーエンドのエラーハンドリング"""
        # 回復成功のハンドラー
        def recovery_handler(error_info):
            return True  # 回復成功
        
        handler = GlobalErrorHandler("TestApp")
        handler.recovery.register_handler(ErrorCategory.APPLICATION, recovery_handler)
        
        exception = ValueError("test error")
        result = handler.handle_error(
            exception,
            ErrorLevel.ERROR,
            ErrorCategory.APPLICATION,
            context={"test": True},
            show_dialog=True,
            attempt_recovery=True
        )
        
        # 回復成功により結果はTrue
        assert result is True
        
        # 回復成功時はダイアログ表示されない
        mock_messagebox.showerror.assert_not_called()

    def test_error_logging_and_history(self):
        """エラーログと履歴の統合テスト"""
        logger = ErrorLogger(self.temp_dir, "IntegrationTest")
        
        # 複数のエラーをログ
        errors = [
            ErrorInfo(ErrorLevel.WARNING, ErrorCategory.CONFIG, "設定警告"),
            ErrorInfo(ErrorLevel.ERROR, ErrorCategory.FILE_IO, "ファイルエラー"),
            ErrorInfo(ErrorLevel.CRITICAL, ErrorCategory.SYSTEM, "システムエラー")
        ]
        
        for error in errors:
            logger.log_error(error)
        
        # 履歴確認
        history = logger.get_error_history()
        assert len(history) == 3
        
        # レベル別の確認
        levels = [e.level for e in history]
        assert ErrorLevel.WARNING in levels
        assert ErrorLevel.ERROR in levels
        assert ErrorLevel.CRITICAL in levels