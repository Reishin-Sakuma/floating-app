"""
パフォーマンス監視・最適化機能
"""
import gc
import os
import sys
import time
import psutil
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class PerformanceMetrics:
    """パフォーマンス指標"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    thread_count: int = 0
    handle_count: int = 0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    response_time_ms: float = 0.0


@dataclass
class PerformanceThresholds:
    """パフォーマンス閾値"""
    max_cpu_percent: float = 10.0
    max_memory_mb: float = 100.0
    max_memory_percent: float = 5.0
    max_response_time_ms: float = 1000.0
    max_thread_count: int = 20
    max_handle_count: int = 1000


class PerformanceCollector:
    """パフォーマンス情報収集クラス"""
    
    def __init__(self):
        """パフォーマンス収集の初期化"""
        self.process = psutil.Process()
        self._last_disk_io = None
        self._startup_time = time.time()
    
    def collect_metrics(self) -> PerformanceMetrics:
        """現在のパフォーマンス指標を収集"""
        try:
            # CPU使用率
            cpu_percent = self.process.cpu_percent()
            
            # メモリ使用量
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = self.process.memory_percent()
            
            # ディスクI/O
            disk_io_read_mb = 0.0
            disk_io_write_mb = 0.0
            try:
                current_io = self.process.io_counters()
                if self._last_disk_io:
                    read_diff = current_io.read_bytes - self._last_disk_io.read_bytes
                    write_diff = current_io.write_bytes - self._last_disk_io.write_bytes
                    disk_io_read_mb = read_diff / (1024 * 1024)
                    disk_io_write_mb = write_diff / (1024 * 1024)
                self._last_disk_io = current_io
            except Exception:
                pass
            
            # スレッド数
            thread_count = self.process.num_threads()
            
            # ハンドル数（Windows）
            handle_count = 0
            try:
                if hasattr(self.process, 'num_handles'):
                    handle_count = self.process.num_handles()
            except Exception:
                pass
            
            # ガベージコレクション統計
            gc_collections = {}
            for i in range(3):  # 3世代のGC統計
                gc_collections[i] = gc.get_count()[i]
            
            return PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
                thread_count=thread_count,
                handle_count=handle_count,
                gc_collections=gc_collections
            )
            
        except Exception as e:
            # エラー時はデフォルト値
            return PerformanceMetrics()
    
    def get_startup_time(self) -> float:
        """アプリケーション起動時間を取得（秒）"""
        return time.time() - self._startup_time
    
    def measure_response_time(self, func: Callable, *args, **kwargs) -> tuple:
        """関数の応答時間を測定"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = e
            success = False
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # ミリ秒
        return result, response_time, success


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        """パフォーマンス監視の初期化"""
        self.collector = PerformanceCollector()
        self.thresholds = thresholds or PerformanceThresholds()
        self._history = []
        self._max_history = 1000
        self._monitoring = False
        self._monitor_thread = None
        self._monitor_interval = 5.0  # 5秒間隔
        self._alert_callbacks = []
        self._performance_callbacks = []
    
    def start_monitoring(self, interval: float = 5.0) -> bool:
        """監視を開始"""
        if self._monitoring:
            return True
        
        try:
            self._monitor_interval = interval
            self._monitoring = True
            
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self._monitor_thread.start()
            
            return True
            
        except Exception:
            self._monitoring = False
            return False
    
    def stop_monitoring(self) -> None:
        """監視を停止"""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self) -> None:
        """監視ループ（別スレッドで実行）"""
        while self._monitoring:
            try:
                metrics = self.collector.collect_metrics()
                
                # 履歴に追加
                self._add_to_history(metrics)
                
                # 閾値チェック
                violations = self._check_thresholds(metrics)
                if violations:
                    self._trigger_alerts(metrics, violations)
                
                # パフォーマンスコールバック実行
                self._trigger_performance_callbacks(metrics)
                
                time.sleep(self._monitor_interval)
                
            except Exception:
                time.sleep(self._monitor_interval)
    
    def _add_to_history(self, metrics: PerformanceMetrics) -> None:
        """履歴に追加"""
        self._history.append(metrics)
        if len(self._history) > self._max_history:
            self._history.pop(0)
    
    def _check_thresholds(self, metrics: PerformanceMetrics) -> List[str]:
        """閾値チェック"""
        violations = []
        
        if metrics.cpu_percent > self.thresholds.max_cpu_percent:
            violations.append(f"CPU使用率が閾値を超過: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_mb > self.thresholds.max_memory_mb:
            violations.append(f"メモリ使用量が閾値を超過: {metrics.memory_mb:.1f}MB")
        
        if metrics.memory_percent > self.thresholds.max_memory_percent:
            violations.append(f"メモリ使用率が閾値を超過: {metrics.memory_percent:.1f}%")
        
        if metrics.response_time_ms > self.thresholds.max_response_time_ms:
            violations.append(f"応答時間が閾値を超過: {metrics.response_time_ms:.1f}ms")
        
        if metrics.thread_count > self.thresholds.max_thread_count:
            violations.append(f"スレッド数が閾値を超過: {metrics.thread_count}")
        
        if metrics.handle_count > self.thresholds.max_handle_count:
            violations.append(f"ハンドル数が閾値を超過: {metrics.handle_count}")
        
        return violations
    
    def _trigger_alerts(self, metrics: PerformanceMetrics, violations: List[str]) -> None:
        """アラートをトリガー"""
        for callback in self._alert_callbacks:
            try:
                callback(metrics, violations)
            except Exception:
                pass
    
    def _trigger_performance_callbacks(self, metrics: PerformanceMetrics) -> None:
        """パフォーマンスコールバックをトリガー"""
        for callback in self._performance_callbacks:
            try:
                callback(metrics)
            except Exception:
                pass
    
    def add_alert_callback(self, callback: Callable[[PerformanceMetrics, List[str]], None]) -> None:
        """アラートコールバックを追加"""
        self._alert_callbacks.append(callback)
    
    def add_performance_callback(self, callback: Callable[[PerformanceMetrics], None]) -> None:
        """パフォーマンスコールバックを追加"""
        self._performance_callbacks.append(callback)
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """現在の指標を取得"""
        return self.collector.collect_metrics()
    
    def get_history(self, minutes: Optional[int] = None) -> List[PerformanceMetrics]:
        """履歴を取得"""
        if minutes is None:
            return self._history.copy()
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self._history if m.timestamp >= cutoff_time]
    
    def get_average_metrics(self, minutes: Optional[int] = None) -> Optional[PerformanceMetrics]:
        """平均指標を取得"""
        history = self.get_history(minutes)
        if not history:
            return None
        
        count = len(history)
        return PerformanceMetrics(
            cpu_percent=sum(m.cpu_percent for m in history) / count,
            memory_mb=sum(m.memory_mb for m in history) / count,
            memory_percent=sum(m.memory_percent for m in history) / count,
            disk_io_read_mb=sum(m.disk_io_read_mb for m in history) / count,
            disk_io_write_mb=sum(m.disk_io_write_mb for m in history) / count,
            thread_count=int(sum(m.thread_count for m in history) / count),
            handle_count=int(sum(m.handle_count for m in history) / count),
            response_time_ms=sum(m.response_time_ms for m in history) / count
        )
    
    def clear_history(self) -> None:
        """履歴をクリア"""
        self._history.clear()


class PerformanceOptimizer:
    """パフォーマンス最適化クラス"""
    
    def __init__(self):
        """パフォーマンス最適化の初期化"""
        self._optimization_history = []
        self._last_gc_time = time.time()
        self._gc_threshold = 60  # 60秒間隔でGC
    
    def optimize_memory(self) -> Dict[str, Any]:
        """メモリ最適化を実行"""
        start_time = time.time()
        result = {
            "timestamp": datetime.now(),
            "optimizations": [],
            "before_memory_mb": 0.0,
            "after_memory_mb": 0.0,
            "memory_saved_mb": 0.0
        }
        
        try:
            # 実行前メモリ使用量
            process = psutil.Process()
            before_memory = process.memory_info().rss / (1024 * 1024)
            result["before_memory_mb"] = before_memory
            
            # ガベージコレクション強制実行
            collected_counts = []
            for generation in range(3):
                collected = gc.collect(generation)
                collected_counts.append(collected)
            
            if any(collected_counts):
                result["optimizations"].append(f"ガベージコレクション実行: {collected_counts}")
            
            # 実行後メモリ使用量
            after_memory = process.memory_info().rss / (1024 * 1024)
            result["after_memory_mb"] = after_memory
            result["memory_saved_mb"] = before_memory - after_memory
            
            self._last_gc_time = time.time()
            
        except Exception as e:
            result["error"] = str(e)
        
        self._optimization_history.append(result)
        return result
    
    def optimize_threads(self) -> Dict[str, Any]:
        """スレッド最適化を実行"""
        result = {
            "timestamp": datetime.now(),
            "optimizations": [],
            "before_thread_count": 0,
            "after_thread_count": 0
        }
        
        try:
            # 実行前スレッド数
            process = psutil.Process()
            before_threads = process.num_threads()
            result["before_thread_count"] = before_threads
            
            # 不要なスレッドの検出と整理
            active_threads = threading.active_count()
            
            # デーモンスレッドの確認
            daemon_threads = sum(1 for t in threading.enumerate() if t.daemon)
            
            result["optimizations"].append(f"アクティブスレッド数: {active_threads}")
            result["optimizations"].append(f"デーモンスレッド数: {daemon_threads}")
            
            # 実行後スレッド数
            after_threads = process.num_threads()
            result["after_thread_count"] = after_threads
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def optimize_disk_cache(self) -> Dict[str, Any]:
        """ディスクキャッシュ最適化を実行"""
        result = {
            "timestamp": datetime.now(),
            "optimizations": [],
            "temp_files_cleaned": 0,
            "cache_size_mb": 0.0
        }
        
        try:
            # 一時ファイルのクリーンアップ
            temp_dir = Path.home() / "AppData" / "Local" / "Temp"
            cleaned_count = 0
            total_size = 0
            
            if temp_dir.exists():
                # アプリ固有の一時ファイルを削除
                app_temp_pattern = "*floating*launcher*"
                for temp_file in temp_dir.glob(app_temp_pattern):
                    try:
                        if temp_file.is_file() and (datetime.now() - datetime.fromtimestamp(temp_file.stat().st_mtime)).days > 1:
                            size = temp_file.stat().st_size
                            temp_file.unlink()
                            cleaned_count += 1
                            total_size += size
                    except Exception:
                        pass
            
            result["temp_files_cleaned"] = cleaned_count
            result["cache_size_mb"] = total_size / (1024 * 1024)
            
            if cleaned_count > 0:
                result["optimizations"].append(f"一時ファイル削除: {cleaned_count}個")
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def auto_optimize(self, metrics: PerformanceMetrics, thresholds: PerformanceThresholds) -> Dict[str, Any]:
        """自動最適化を実行"""
        result = {
            "timestamp": datetime.now(),
            "optimizations_performed": [],
            "triggered_by": []
        }
        
        # メモリ使用量が閾値を超えた場合
        if metrics.memory_mb > thresholds.max_memory_mb or metrics.memory_percent > thresholds.max_memory_percent:
            memory_result = self.optimize_memory()
            result["optimizations_performed"].append("memory")
            result["triggered_by"].append("high_memory_usage")
            result["memory_optimization"] = memory_result
        
        # 定期的なガベージコレクション
        if time.time() - self._last_gc_time > self._gc_threshold:
            memory_result = self.optimize_memory()
            result["optimizations_performed"].append("scheduled_gc")
            result["memory_optimization"] = memory_result
        
        # スレッド数が多い場合
        if metrics.thread_count > thresholds.max_thread_count:
            thread_result = self.optimize_threads()
            result["optimizations_performed"].append("threads")
            result["triggered_by"].append("high_thread_count")
            result["thread_optimization"] = thread_result
        
        return result
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """最適化履歴を取得"""
        return self._optimization_history.copy()


class PerformanceReporter:
    """パフォーマンスレポート生成クラス"""
    
    def __init__(self, monitor: PerformanceMonitor):
        """レポート生成の初期化"""
        self.monitor = monitor
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """サマリーレポートを生成"""
        current = self.monitor.get_current_metrics()
        history = self.monitor.get_history()
        
        if not history:
            return {"error": "履歴データがありません"}
        
        # 統計計算
        cpu_values = [m.cpu_percent for m in history]
        memory_values = [m.memory_mb for m in history]
        
        report = {
            "timestamp": datetime.now(),
            "current_metrics": {
                "cpu_percent": current.cpu_percent,
                "memory_mb": current.memory_mb,
                "memory_percent": current.memory_percent,
                "thread_count": current.thread_count,
                "handle_count": current.handle_count
            },
            "statistics": {
                "cpu": {
                    "current": current.cpu_percent,
                    "average": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory": {
                    "current_mb": current.memory_mb,
                    "average_mb": sum(memory_values) / len(memory_values),
                    "max_mb": max(memory_values),
                    "min_mb": min(memory_values)
                }
            },
            "uptime_seconds": self.monitor.collector.get_startup_time(),
            "data_points": len(history)
        }
        
        return report
    
    def generate_performance_trends(self, minutes: int = 60) -> Dict[str, Any]:
        """パフォーマンストレンドを生成"""
        history = self.monitor.get_history(minutes)
        
        if len(history) < 2:
            return {"error": "トレンド分析に十分なデータがありません"}
        
        # トレンド計算
        cpu_trend = self._calculate_trend([m.cpu_percent for m in history])
        memory_trend = self._calculate_trend([m.memory_mb for m in history])
        
        return {
            "period_minutes": minutes,
            "data_points": len(history),
            "trends": {
                "cpu_percent": cpu_trend,
                "memory_mb": memory_trend
            },
            "recommendations": self._generate_recommendations(history)
        }
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """トレンドを計算"""
        if len(values) < 2:
            return {"direction": 0.0, "slope": 0.0}
        
        # 線形回帰によるトレンド計算の簡易版
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        return {
            "direction": 1 if slope > 0 else -1 if slope < 0 else 0,
            "slope": slope
        }
    
    def _generate_recommendations(self, history: List[PerformanceMetrics]) -> List[str]:
        """推奨事項を生成"""
        recommendations = []
        
        if not history:
            return recommendations
        
        # CPU使用率が高い場合
        avg_cpu = sum(m.cpu_percent for m in history) / len(history)
        if avg_cpu > 5.0:
            recommendations.append("CPU使用率が高めです。不要なプロセスを確認してください。")
        
        # メモリ使用量が増加傾向の場合
        memory_values = [m.memory_mb for m in history]
        memory_trend = self._calculate_trend(memory_values)
        if memory_trend["slope"] > 0.1:
            recommendations.append("メモリ使用量が増加傾向です。メモリリークの可能性があります。")
        
        # スレッド数が多い場合
        avg_threads = sum(m.thread_count for m in history) / len(history)
        if avg_threads > 10:
            recommendations.append("スレッド数が多めです。スレッドプールの最適化を検討してください。")
        
        return recommendations