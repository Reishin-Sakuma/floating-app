#!/usr/bin/env python3
"""
フローティングランチャー ビルドスクリプト
"""
import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime
import hashlib


class BuildSystem:
    """ビルドシステムクラス"""
    
    def __init__(self):
        """ビルドシステムの初期化"""
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.assets_dir = self.project_root / "assets"
        self.spec_file = self.project_root / "build.spec"
        
        # ビルド情報
        self.app_name = "FloatingLauncher"
        self.version = "1.0.0"
        self.build_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def clean(self):
        """クリーンビルド（既存のビルド成果物を削除）"""
        print("🧹 クリーンビルドを実行中...")
        
        # 削除対象ディレクトリ
        cleanup_dirs = [self.dist_dir, self.build_dir]
        
        for dir_path in cleanup_dirs:
            if dir_path.exists():
                print(f"  削除中: {dir_path}")
                shutil.rmtree(dir_path)
        
        # __pycache__ディレクトリも削除
        for pycache in self.project_root.rglob("__pycache__"):
            if pycache.is_dir():
                print(f"  削除中: {pycache}")
                shutil.rmtree(pycache)
        
        print("✅ クリーンアップ完了")
    
    def check_dependencies(self):
        """依存関係チェック"""
        print("📋 依存関係をチェック中...")
        
        required_modules = [
            "pyinstaller",
            "psutil",
            "tkinter"
        ]
        
        missing_modules = []
        
        for module in required_modules:
            try:
                if module == "tkinter":
                    import tkinter
                else:
                    __import__(module)
                print(f"  ✅ {module}")
            except ImportError:
                print(f"  ❌ {module}")
                missing_modules.append(module)
        
        if missing_modules:
            print(f"\n❌ 不足している依存関係: {', '.join(missing_modules)}")
            print("以下のコマンドで依存関係をインストールしてください:")
            print(f"pip install {' '.join(missing_modules)}")
            return False
        
        print("✅ 依存関係チェック完了")
        return True
    
    def create_assets(self):
        """アセット（アイコンなど）を作成"""
        print("🎨 アセットを作成中...")
        
        # assetsディレクトリを作成
        self.assets_dir.mkdir(exist_ok=True)
        
        # 簡易的なアイコンファイルを作成（実際のプロジェクトでは適切なアイコンを使用）
        icon_path = self.assets_dir / "icon.ico"
        if not icon_path.exists():
            print("  デフォルトアイコンを作成中...")
            self._create_default_icon(icon_path)
        
        print("✅ アセット作成完了")
    
    def _create_default_icon(self, icon_path: Path):
        """デフォルトアイコンを作成"""
        try:
            from PIL import Image, ImageDraw
            
            # 32x32のシンプルなアイコンを作成
            size = 32
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # 青い円を描画
            margin = 4
            draw.ellipse(
                [margin, margin, size - margin, size - margin],
                fill=(74, 144, 226, 255),
                outline=(46, 91, 186, 255)
            )
            
            # 中央に白い四角
            center = size // 2
            symbol_size = 6
            draw.rectangle([
                center - symbol_size//2, center - symbol_size//2,
                center + symbol_size//2, center + symbol_size//2
            ], fill=(255, 255, 255, 255))
            
            # ICO形式で保存
            image.save(icon_path, format='ICO')
            print(f"    作成完了: {icon_path}")
            
        except ImportError:
            # PILが使用できない場合はダミーファイル作成
            icon_path.write_bytes(b'\x00\x01\x02\x03')  # ダミーデータ
            print(f"    ダミーアイコン作成: {icon_path}")
        except Exception as e:
            print(f"    アイコン作成エラー: {e}")
    
    def build_executable(self):
        """実行ファイルをビルド"""
        print("🔨 実行ファイルをビルド中...")
        
        # PyInstallerコマンドを構築
        cmd = [
            sys.executable, "-m", "pyinstaller",
            str(self.spec_file),
            "--clean",
            "--noconfirm"
        ]
        
        print(f"  実行コマンド: {' '.join(cmd)}")
        
        # ビルド実行
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分でタイムアウト
            )
            
            if result.returncode == 0:
                print("✅ ビルド成功")
                return True
            else:
                print("❌ ビルド失敗")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ ビルドタイムアウト（5分）")
            return False
        except Exception as e:
            print(f"❌ ビルドエラー: {e}")
            return False
    
    def verify_build(self):
        """ビルド成果物の検証"""
        print("🔍 ビルド成果物を検証中...")
        
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        
        if not exe_path.exists():
            print(f"❌ 実行ファイルが見つかりません: {exe_path}")
            return False
        
        # ファイルサイズチェック
        file_size = exe_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"  実行ファイル: {exe_path}")
        print(f"  ファイルサイズ: {file_size_mb:.1f} MB")
        
        # サイズが妥当かチェック
        if file_size_mb > 100:  # 100MB以上は警告
            print(f"⚠️  ファイルサイズが大きいです: {file_size_mb:.1f} MB")
        elif file_size_mb < 5:  # 5MB未満は警告
            print(f"⚠️  ファイルサイズが小さすぎます: {file_size_mb:.1f} MB")
        
        # 実行可能かチェック（基本的な起動テスト）
        print("  実行テストを実行中...")
        try:
            test_result = subprocess.run(
                [str(exe_path), "--test"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if test_result.returncode == 0:
                print("  ✅ 実行テスト成功")
                return True
            else:
                print("  ❌ 実行テスト失敗")
                print("  STDOUT:", test_result.stdout)
                print("  STDERR:", test_result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("  ⚠️  実行テストタイムアウト")
            return False
        except Exception as e:
            print(f"  ❌ 実行テストエラー: {e}")
            return False
    
    def create_distribution_package(self):
        """配布パッケージを作成"""
        print("📦 配布パッケージを作成中...")
        
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        if not exe_path.exists():
            print("❌ 実行ファイルが見つかりません")
            return False
        
        # 配布ファイル名
        package_name = f"{self.app_name}_v{self.version}_{self.build_date}"
        package_dir = self.dist_dir / package_name
        package_zip = self.dist_dir / f"{package_name}.zip"
        
        try:
            # パッケージディレクトリ作成
            if package_dir.exists():
                shutil.rmtree(package_dir)
            package_dir.mkdir()
            
            # ファイルをコピー
            files_to_include = [
                (exe_path, package_dir / exe_path.name),
                (self.project_root / "README.md", package_dir / "README.md"),
                (self.project_root / "config.json", package_dir / "config.json")
            ]
            
            for src, dst in files_to_include:
                if src.exists():
                    if src.is_file():
                        shutil.copy2(src, dst)
                        print(f"  追加: {src.name}")
            
            # インストール手順を作成
            install_txt = package_dir / "インストール手順.txt"
            install_content = f"""
フローティングランチャー v{self.version}

【インストール手順】
1. {self.app_name}.exe を任意のフォルダに配置してください
2. config.json を必要に応じて編集してください
3. {self.app_name}.exe をダブルクリックして起動してください

【アンインストール手順】
1. タスクマネージャーからアプリケーションを終了してください
2. 配置したフォルダを削除してください

【システム要件】
- Windows 10 / 11
- .NET Framework は不要

【問い合わせ】
不具合やご要望がございましたら、開発者にご連絡ください。

ビルド日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
"""
            install_txt.write_text(install_content, encoding='utf-8')
            
            # ZIPファイル作成
            with zipfile.ZipFile(package_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(package_dir)
                        zipf.write(file_path, arcname)
                        print(f"  ZIP追加: {arcname}")
            
            # ハッシュ値計算
            hash_file = self.dist_dir / f"{package_name}.sha256"
            sha256_hash = self._calculate_file_hash(package_zip)
            hash_content = f"{sha256_hash}  {package_zip.name}\n"
            hash_file.write_text(hash_content)
            
            print(f"✅ 配布パッケージ作成完了")
            print(f"  パッケージ: {package_zip}")
            print(f"  ハッシュ: {hash_file}")
            print(f"  SHA256: {sha256_hash}")
            
            return True
            
        except Exception as e:
            print(f"❌ パッケージ作成エラー: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルのSHA256ハッシュを計算"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def build_all(self, clean_build=True):
        """完全ビルドプロセス"""
        print(f"🚀 フローティングランチャー v{self.version} ビルド開始")
        print(f"📅 ビルド日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        steps = [
            ("依存関係チェック", self.check_dependencies),
            ("アセット作成", self.create_assets),
        ]
        
        if clean_build:
            steps.insert(0, ("クリーンビルド", self.clean))
        
        steps.extend([
            ("実行ファイルビルド", self.build_executable),
            ("ビルド検証", self.verify_build),
            ("配布パッケージ作成", self.create_distribution_package)
        ])
        
        # ステップ実行
        for step_name, step_func in steps:
            print(f"\n📍 {step_name}")
            if not step_func():
                print(f"❌ {step_name} 失敗 - ビルド中止")
                return False
        
        print("\n" + "=" * 60)
        print("🎉 ビルド完了!")
        print(f"📂 成果物: {self.dist_dir}")
        
        return True


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="フローティングランチャー ビルドスクリプト")
    parser.add_argument("--clean", action="store_true", help="クリーンビルドを実行")
    parser.add_argument("--no-package", action="store_true", help="配布パッケージを作成しない")
    
    args = parser.parse_args()
    
    builder = BuildSystem()
    
    try:
        success = builder.build_all(clean_build=args.clean)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  ビルドが中止されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()