#!/usr/bin/env python3
"""
フローティングアイコンランチャー メインアプリケーション
"""
import sys
import os
import tkinter as tk
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config_manager import ConfigManager
from app_launcher import AppLauncher
from floating_icon import FloatingIcon
from settings_window import SettingsWindow
from system_tray import SystemTrayManager


class FloatingLauncher:
    """フローティングランチャー メインアプリケーション"""
    
    def __init__(self):
        """アプリケーションの初期化"""
        self.root = tk.Tk()
        self.root.withdraw()  # メインウィンドウを非表示
        
        # コンポーネント初期化
        self.config_manager = ConfigManager()
        self.app_launcher = AppLauncher()
        self.floating_icon = FloatingIcon(self.config_manager)
        self.settings_window = None
        self.system_tray = SystemTrayManager("フローティングランチャー")
        
        # イベントハンドラ設定
        self.floating_icon.set_click_callback(self._on_icon_click)
        self.floating_icon.set_right_click_callback(self._on_icon_right_click)
        
        # システムトレイ設定
        self._setup_system_tray()
    
    def run(self):
        """アプリケーション実行"""
        try:
            # システムトレイを開始
            config = self.config_manager.load_config()
            show_tray = config.get('show_tray_icon', True) if config else True
            
            if show_tray and self.system_tray.is_available():
                if self.system_tray.initialize():
                    self.system_tray.start()
                    print("システムトレイアイコンを開始しました")
            
            # フローティングアイコンを表示
            if self.floating_icon.show():
                print("フローティングアイコンランチャーを開始しました")
                
                # メインループ開始
                self.root.mainloop()
            else:
                print("フローティングアイコンの表示に失敗しました")
                return False
                
        except KeyboardInterrupt:
            print("\nアプリケーションを終了します")
            self._cleanup()
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            self._cleanup()
            return False
            
        return True
    
    def _on_icon_click(self):
        """アイコンクリック時の処理"""
        try:
            config = self.config_manager.load_config()
            if config and 'app_path' in config:
                app_path = config['app_path']
                if app_path and app_path.strip():
                    print(f"アプリケーションを起動します: {app_path}")
                    result = self.app_launcher.launch_application(app_path)
                    if result.success:
                        print(f"アプリケーション起動成功 (PID: {result.process_id})")
                    else:
                        print(f"アプリケーション起動失敗: {result.error_message}")
                        self._show_settings()
                else:
                    print("アプリケーションパスが設定されていません")
                    self._show_settings()
            else:
                print("設定が見つからないため設定画面を開きます")
                self._show_settings()
        except Exception as e:
            print(f"アプリケーション起動エラー: {e}")
            self._show_settings()
    
    def _on_icon_right_click(self):
        """アイコン右クリック時の処理"""
        self._show_settings()
    
    def _show_settings(self):
        """設定画面を表示"""
        try:
            if not self.settings_window:
                self.settings_window = SettingsWindow(self.config_manager)
                self.settings_window.set_callback('apply', self._on_settings_applied)
            
            self.settings_window.show()
            
        except Exception as e:
            print(f"設定画面表示エラー: {e}")
    
    def _on_settings_applied(self, config):
        """設定適用時の処理"""
        try:
            # フローティングアイコンの設定を更新
            if 'icon_position' in config:
                pos = config['icon_position']
                if isinstance(pos, dict) and 'x' in pos and 'y' in pos:
                    self.floating_icon.update_position(pos['x'], pos['y'])
            
            if 'icon_size' in config:
                self.floating_icon.update_size(config['icon_size'])
            
            # フローティングアイコンを再表示してイベントハンドリングを確実にする
            self.floating_icon.hide()
            self.floating_icon.show()
            
            print("設定が適用されました")
            
        except Exception as e:
            print(f"設定適用エラー: {e}")
    
    def _setup_system_tray(self):
        """システムトレイを設定"""
        try:
            if self.system_tray.is_available():
                callbacks = {
                    'settings': self._on_tray_settings,
                    'exit': self._on_tray_exit
                }
                self.system_tray.set_callbacks(callbacks)
        except Exception as e:
            print(f"システムトレイ設定エラー: {e}")
    
    def _on_tray_settings(self):
        """システムトレイ設定メニュークリック処理"""
        self._show_settings()
    
    def _on_tray_exit(self):
        """システムトレイ終了メニュークリック処理"""
        self._cleanup()
    
    def _cleanup(self):
        """クリーンアップ処理"""
        try:
            if self.system_tray:
                self.system_tray.stop()
            
            if self.floating_icon:
                self.floating_icon.hide()
            
            if self.settings_window:
                self.settings_window.destroy()
                
            self.root.quit()
            
        except Exception as e:
            print(f"クリーンアップエラー: {e}")


def main():
    """メイン関数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # テストモード: 基本機能確認のみ
        print("=== フローティングランチャー テストモード ===")
        
        try:
            # 各コンポーネントの基本初期化テスト
            config_manager = ConfigManager()
            print("OK ConfigManager 初期化成功")
            
            app_launcher = AppLauncher()
            print("OK AppLauncher 初期化成功")
            
            floating_icon = FloatingIcon(config_manager)
            print("OK FloatingIcon 初期化成功")
            
            settings_window = SettingsWindow(config_manager)
            print("OK SettingsWindow 初期化成功")
            
            system_tray = SystemTrayManager("テストアプリ")
            print("OK SystemTrayManager 初期化成功")
            print(f"   システムトレイ利用可否: {'可能' if system_tray.is_available() else '不可'}")
            
            print("\n=== 基本機能テスト完了 ===")
            print("すべてのコンポーネントが正常に初期化されました")
            
        except Exception as e:
            print(f"NG テストエラー: {e}")
            return False
            
        return True
    
    else:
        # 通常モード: フルアプリケーション起動
        app = FloatingLauncher()
        return app.run()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)