"""
Windows自動起動機能
"""
import os
import sys
import winreg
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class AutoStartupInfo:
    """自動起動情報"""
    enabled: bool
    app_name: str
    app_path: str
    registry_key: str
    error: Optional[str] = None


class WindowsAutoStartup:
    """Windows自動起動管理クラス"""
    
    # レジストリキーのパス
    STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def __init__(self, app_name: str = "FloatingLauncher"):
        """自動起動管理の初期化"""
        self.app_name = app_name
        self._app_path = self._get_current_executable_path()
    
    def is_enabled(self) -> Tuple[bool, Optional[str]]:
        """自動起動が有効かチェック"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.STARTUP_KEY) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    # パスが現在の実行ファイルと一致するかチェック
                    return value == self._app_path, None
                except FileNotFoundError:
                    return False, None
                    
        except Exception as e:
            return False, f"レジストリアクセスエラー: {str(e)}"
    
    def enable(self) -> Tuple[bool, Optional[str]]:
        """自動起動を有効にする"""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                self.STARTUP_KEY, 
                0, 
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(
                    key, 
                    self.app_name, 
                    0, 
                    winreg.REG_SZ, 
                    self._app_path
                )
                return True, None
                
        except Exception as e:
            return False, f"自動起動の有効化に失敗: {str(e)}"
    
    def disable(self) -> Tuple[bool, Optional[str]]:
        """自動起動を無効にする"""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                self.STARTUP_KEY, 
                0, 
                winreg.KEY_SET_VALUE
            ) as key:
                try:
                    winreg.DeleteValue(key, self.app_name)
                    return True, None
                except FileNotFoundError:
                    # 既に削除されている場合は成功とみなす
                    return True, None
                    
        except Exception as e:
            return False, f"自動起動の無効化に失敗: {str(e)}"
    
    def get_info(self) -> AutoStartupInfo:
        """自動起動の詳細情報を取得"""
        enabled, error = self.is_enabled()
        
        return AutoStartupInfo(
            enabled=enabled,
            app_name=self.app_name,
            app_path=self._app_path,
            registry_key=self.STARTUP_KEY,
            error=error
        )
    
    def toggle(self) -> Tuple[bool, bool, Optional[str]]:
        """自動起動の有効/無効を切り替え"""
        enabled, error = self.is_enabled()
        
        if error:
            return False, False, error
        
        if enabled:
            success, error = self.disable()
            return success, False, error
        else:
            success, error = self.enable()
            return success, True, error
    
    def _get_current_executable_path(self) -> str:
        """現在の実行ファイルのパスを取得"""
        try:
            # PyInstallerでパッケージ化されている場合
            if hasattr(sys, '_MEIPASS'):
                return sys.executable
            
            # Pythonスクリプトとして実行されている場合
            if sys.argv and sys.argv[0]:
                script_path = os.path.abspath(sys.argv[0])
                
                # .pyファイルの場合はPython経由で実行するコマンドラインを作成
                if script_path.endswith('.py'):
                    python_exe = sys.executable
                    return f'"{python_exe}" "{script_path}"'
                
                return script_path
            
            # フォールバック
            return sys.executable
            
        except Exception:
            # 最終フォールバック
            return sys.executable
    
    def validate_path(self, path: str) -> Tuple[bool, Optional[str]]:
        """指定されたパスの有効性を検証"""
        try:
            if not path:
                return False, "パスが空です"
            
            # 引用符で囲まれたコマンドラインの場合の処理
            if path.startswith('"') and '" "' in path:
                # Python + スクリプトファイルのコマンドライン
                parts = path.split('" "', 1)
                python_path = parts[0].strip('"')
                script_path = parts[1].strip('"')
                
                if not os.path.exists(python_path):
                    return False, f"Python実行ファイルが見つかりません: {python_path}"
                
                if not os.path.exists(script_path):
                    return False, f"スクリプトファイルが見つかりません: {script_path}"
                
                return True, None
            
            # 単一の実行ファイルの場合
            if not os.path.exists(path):
                return False, f"ファイルが見つかりません: {path}"
            
            if not os.path.isfile(path):
                return False, f"指定されたパスはファイルではありません: {path}"
            
            return True, None
            
        except Exception as e:
            return False, f"パス検証エラー: {str(e)}"


class AutoStartupManager:
    """自動起動マネージャー（高レベルAPI）"""
    
    def __init__(self, app_name: str = "FloatingLauncher"):
        """自動起動マネージャーの初期化"""
        self.app_name = app_name
        self._startup = WindowsAutoStartup(app_name)
    
    def is_supported(self) -> bool:
        """自動起動機能がサポートされているかチェック"""
        try:
            # Windowsかチェック
            return os.name == 'nt'
        except Exception:
            return False
    
    def get_status(self) -> AutoStartupInfo:
        """自動起動の状態を取得"""
        if not self.is_supported():
            return AutoStartupInfo(
                enabled=False,
                app_name=self.app_name,
                app_path="",
                registry_key="",
                error="Windowsでのみサポートされています"
            )
        
        return self._startup.get_info()
    
    def set_enabled(self, enabled: bool) -> Tuple[bool, Optional[str]]:
        """自動起動の有効/無効を設定"""
        if not self.is_supported():
            return False, "Windowsでのみサポートされています"
        
        current_enabled, error = self._startup.is_enabled()
        
        if error:
            return False, error
        
        # 既に希望する状態の場合は何もしない
        if current_enabled == enabled:
            return True, None
        
        if enabled:
            return self._startup.enable()
        else:
            return self._startup.disable()
    
    def toggle_startup(self) -> Tuple[bool, bool, Optional[str]]:
        """自動起動を切り替え"""
        if not self.is_supported():
            return False, False, "Windowsでのみサポートされています"
        
        return self._startup.toggle()
    
    def validate_installation(self) -> Tuple[bool, Optional[str]]:
        """現在のインストール状態を検証"""
        if not self.is_supported():
            return False, "Windowsでのみサポートされています"
        
        info = self._startup.get_info()
        
        if info.error:
            return False, info.error
        
        return self._startup.validate_path(info.app_path)
    
    def repair_startup(self) -> Tuple[bool, Optional[str]]:
        """自動起動設定を修復"""
        if not self.is_supported():
            return False, "Windowsでのみサポートされています"
        
        try:
            # 現在の状態を取得
            info = self.get_status()
            
            if info.enabled:
                # 一度無効化してから再度有効化
                success, error = self._startup.disable()
                if not success:
                    return False, f"無効化に失敗: {error}"
                
                success, error = self._startup.enable()
                if not success:
                    return False, f"再有効化に失敗: {error}"
                
                return True, "自動起動設定を修復しました"
            else:
                return True, "修復の必要はありません"
                
        except Exception as e:
            return False, f"修復処理でエラーが発生: {str(e)}"