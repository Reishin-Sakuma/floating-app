"""
設定ファイル管理システム

JSONベースの設定ファイルを管理するConfigManagerクラス。
設定値の読み書き、バリデーション、デフォルト設定の提供、
エラー処理を行う。
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


class ConfigManager:
    """設定ファイル管理クラス"""

    def __init__(self, config_file_path: Optional[str] = None):
        """
        設定管理クラスの初期化
        
        Args:
            config_file_path: 設定ファイルパス。未指定時はデフォルトパスを使用
        """
        if config_file_path is None:
            # デフォルト設定ファイルパス
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            config_dir = os.path.join(app_data, 'FloatingLauncher')
            os.makedirs(config_dir, exist_ok=True)
            self.config_file_path = os.path.join(config_dir, 'config.json')
        else:
            self.config_file_path = config_file_path
            
        # バックアップディレクトリの確保
        self.backup_dir = os.path.join(os.path.dirname(self.config_file_path), 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """
        設定ファイルを読み込み、設定値を返す
        
        Returns:
            設定値の辞書
        """
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # メタデータを除去してから返す（テスト用）
                config_without_metadata = {k: v for k, v in config.items() if k != '_metadata'}
                        
                return config_without_metadata
            else:
                # ファイルが存在しない場合はデフォルト設定で新規作成
                default_config = self.get_default_config()
                self.save_config(default_config)
                return default_config
                
        except json.JSONDecodeError:
            # JSON解析エラー時はバックアップから復旧を試行
            backup_restored = self._try_restore_from_latest_backup()
            if backup_restored:
                return self.load_config()  # 復旧後に再読み込み
            else:
                # バックアップからの復旧も失敗した場合はデフォルト設定を返す
                default_config = self.get_default_config()
                self.save_config(default_config)
                return default_config
        except (OSError, IOError) as e:
            # ファイル読み込みエラー時もデフォルト設定を返す
            return self.get_default_config()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        設定値を設定ファイルに保存する
        
        Args:
            config: 保存する設定値の辞書
            
        Returns:
            保存成功時True、失敗時False
        """
        try:
            # 保存前にバリデーションを実行（基本的な型チェックのみ）
            is_valid, errors = self._basic_validation(config)
            if not is_valid:
                return False
                
            # 既存ファイルがある場合はバックアップを作成
            if os.path.exists(self.config_file_path):
                self.backup_config()
                
            # メタデータを追加
            config_with_metadata = config.copy()
            config_with_metadata['_metadata'] = {
                'last_modified': datetime.now().isoformat(),
                'backup_count': self._get_backup_count()
            }
            
            # 設定ファイルに保存
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_with_metadata, f, indent=2, ensure_ascii=False)
                
            return True
            
        except (OSError, IOError, PermissionError) as e:
            return False

    def get_default_config(self) -> Dict[str, Any]:
        """
        デフォルト設定値を返す
        
        Returns:
            デフォルト設定値の辞書
        """
        return {
            "app_path": "",
            "icon_position": {
                "x": 100,
                "y": 100
            },
            "icon_fixed": False,
            "auto_start": False,
            "icon_size": 32,
            "version": "1.0.0"
        }

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        設定値の妥当性を検証する
        
        Args:
            config: 検証する設定値の辞書
            
        Returns:
            (検証結果, エラーメッセージのリスト)
        """
        errors = []
        
        # 必須キーの存在確認
        required_keys = ["app_path", "icon_position", "icon_fixed", "auto_start", "icon_size", "version"]
        for key in required_keys:
            if key not in config:
                errors.append(f"必須キー '{key}' が存在しません")
                continue
        
        if errors:  # 必須キーがない場合はここで終了
            return False, errors
            
        # app_path の検証
        app_path = config.get("app_path", "")
        if not isinstance(app_path, str):
            errors.append("app_path は文字列である必要があります")
            
        # icon_position の検証
        icon_position = config.get("icon_position", {})
        if not isinstance(icon_position, dict):
            errors.append("icon_position は辞書である必要があります")
        else:
            for coord in ["x", "y"]:
                if coord not in icon_position:
                    errors.append(f"icon_position.{coord} が存在しません")
                elif not isinstance(icon_position[coord], int):
                    errors.append(f"icon_position.{coord} は整数である必要があります")
                elif not (-32768 <= icon_position[coord] <= 32767):
                    errors.append(f"icon_position.{coord} は -32768 から 32767 の範囲内である必要があります")
                    
        # icon_fixed の検証
        if not isinstance(config.get("icon_fixed"), bool):
            errors.append("icon_fixed はブール値である必要があります")
            
        # auto_start の検証
        if not isinstance(config.get("auto_start"), bool):
            errors.append("auto_start はブール値である必要があります")
            
        # icon_size の検証
        icon_size = config.get("icon_size")
        if not isinstance(icon_size, int):
            errors.append("icon_size は整数である必要があります")
        elif not (16 <= icon_size <= 128):
            errors.append("icon_size は 16 から 128 の範囲内である必要があります")
            
        # version の検証
        if not isinstance(config.get("version"), str):
            errors.append("version は文字列である必要があります")
            
        return len(errors) == 0, errors

    def reset_to_default(self) -> bool:
        """
        設定をデフォルトにリセットする
        
        Returns:
            リセット成功時True、失敗時False
        """
        default_config = self.get_default_config()
        return self.save_config(default_config)

    def backup_config(self) -> Optional[str]:
        """
        設定のバックアップを作成し、バックアップファイルパスを返す
        
        Returns:
            バックアップファイルパス。失敗時None
        """
        try:
            if not os.path.exists(self.config_file_path):
                return None
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            shutil.copy2(self.config_file_path, backup_path)
            
            # 古いバックアップファイルを削除（最新5個まで保持）
            self._cleanup_old_backups()
            
            return backup_path
            
        except (OSError, IOError) as e:
            return None

    def restore_from_backup(self, backup_path: str) -> bool:
        """
        バックアップから設定を復元する
        
        Args:
            backup_path: バックアップファイルパス
            
        Returns:
            復元成功時True、失敗時False
        """
        try:
            if not os.path.exists(backup_path):
                return False
                
            # バックアップファイルの内容を読み込み（バリデーションはスキップ）
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_config = json.load(f)
                
            # 現在の設定ファイルを置き換え
            shutil.copy2(backup_path, self.config_file_path)
            
            return True
            
        except (OSError, IOError, json.JSONDecodeError) as e:
            return False

    def _try_restore_from_latest_backup(self) -> bool:
        """
        最新のバックアップから復旧を試行する（内部用メソッド）
        
        Returns:
            復旧成功時True、失敗時False
        """
        try:
            if not os.path.exists(self.backup_dir):
                return False
                
            # バックアップファイル一覧を取得（作成時間順）
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('config_backup_') and filename.endswith('.json'):
                    backup_path = os.path.join(self.backup_dir, filename)
                    backup_files.append((os.path.getmtime(backup_path), backup_path))
                    
            if not backup_files:
                return False
                
            # 最新のバックアップから復旧を試行
            backup_files.sort(reverse=True)
            for _, backup_path in backup_files:
                if self.restore_from_backup(backup_path):
                    return True
                    
            return False
            
        except (OSError, IOError) as e:
            return False

    def _get_backup_count(self) -> int:
        """
        現在のバックアップファイル数を取得する（内部用メソッド）
        
        Returns:
            バックアップファイル数
        """
        try:
            if not os.path.exists(self.backup_dir):
                return 0
                
            backup_files = [f for f in os.listdir(self.backup_dir) 
                          if f.startswith('config_backup_') and f.endswith('.json')]
            return len(backup_files)
            
        except (OSError, IOError):
            return 0

    def _basic_validation(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        保存前の基本的なバリデーション（型チェックのみ）
        
        Args:
            config: 検証する設定値の辞書
            
        Returns:
            (検証結果, エラーメッセージのリスト)
        """
        errors = []
        
        # 基本的な型チェックのみ実行
        if not isinstance(config, dict):
            errors.append("設定は辞書形式である必要があります")
            return False, errors
            
        # 必須キーの型チェック
        type_checks = {
            "app_path": str,
            "icon_position": dict,
            "icon_fixed": bool,
            "auto_start": bool,
            "icon_size": int,
            "version": str
        }
        
        for key, expected_type in type_checks.items():
            if key in config and not isinstance(config[key], expected_type):
                errors.append(f"{key} は {expected_type.__name__} 型である必要があります")
                
        return len(errors) == 0, errors

    def _cleanup_old_backups(self, max_backups: int = 5) -> None:
        """
        古いバックアップファイルを削除する（内部用メソッド）
        
        Args:
            max_backups: 保持する最大バックアップ数
        """
        try:
            if not os.path.exists(self.backup_dir):
                return
                
            # バックアップファイル一覧を取得（作成時間順）
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('config_backup_') and filename.endswith('.json'):
                    backup_path = os.path.join(self.backup_dir, filename)
                    backup_files.append((os.path.getmtime(backup_path), backup_path))
                    
            # 古いファイルから削除
            if len(backup_files) > max_backups:
                backup_files.sort()
                for _, backup_path in backup_files[:-max_backups]:
                    os.remove(backup_path)
                    
        except (OSError, IOError):
            pass  # クリーンアップエラーは無視