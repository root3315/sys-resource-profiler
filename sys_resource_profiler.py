#!/usr/bin/env python3
"""
sys-resource-profiler: Lightweight tool for monitoring system resource
usage and generating performance profiles.
"""

import argparse
import json
import os
import platform
import signal
import sys
import time
from datetime import datetime

import psutil


class ResourceProfiler:
    """Monitors system resources and generates performance profiles."""

    def __init__(self, interval=1.0, duration=10, output_format="text", output_file=None):
        self.interval = interval
        self.duration = duration
        self.output_format = output_format
        self.output_file = output_file
        self.samples = []
        self.memory_timeline = []
        self._running = False

    def start(self):
        """Begin monitoring system resources."""
        self._running = True
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        start_time = time.time()
        iteration = 0

        print(f"Monitoring started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Interval: {self.interval}s, Duration: {self.duration}s")
        print("-" * 60)

        while self._running:
            elapsed = time.time() - start_time
            if self.duration > 0 and elapsed >= self.duration:
                break

            sample = self._collect_sample()
            sample["timestamp"] = datetime.now().isoformat()
            sample["elapsed"] = round(elapsed, 2)
            self.samples.append(sample)

            self.memory_timeline.append({
                "elapsed": round(elapsed, 2),
                "timestamp": sample["timestamp"],
                "mem_used_mb": sample["mem_used_mb"],
                "mem_available_mb": sample["mem_available_mb"],
                "mem_percent": sample["mem_percent"],
                "swap_used_mb": sample["swap_used_mb"],
                "swap_percent": sample["swap_percent"],
            })

            iteration += 1

            if self.output_format == "text":
                self._print_sample(sample, iteration)

            time.sleep(self.interval)

        print("-" * 60)
        print(f"Monitoring stopped after {iteration} samples.")
        return self.samples

    def stop(self):
        """Stop the monitoring loop."""
        self._running = False

    def _handle_signal(self, signum, frame):
        """Handle interrupt signals gracefully."""
        print("\nReceived interrupt signal. Stopping monitoring...")
        self.stop()

    def _collect_sample(self):
        """Collect a single sample of system resource usage."""
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_freq = psutil.cpu_freq()
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage("/")
        net_io = psutil.net_io_counters()
        proc_count = len(psutil.pids())

        sample = {
            "cpu_percent": cpu_percent,
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_freq_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
            "mem_total_mb": round(mem.total / (1024 * 1024), 1),
            "mem_used_mb": round(mem.used / (1024 * 1024), 1),
            "mem_available_mb": round(mem.available / (1024 * 1024), 1),
            "mem_percent": mem.percent,
            "swap_total_mb": round(swap.total / (1024 * 1024), 1),
            "swap_used_mb": round(swap.used / (1024 * 1024), 1),
            "swap_percent": swap.percent,
            "disk_total_gb": round(disk.total / (1024 ** 3), 1),
            "disk_used_gb": round(disk.used / (1024 ** 3), 1),
            "disk_free_gb": round(disk.free / (1024 ** 3), 1),
            "disk_percent": disk.percent,
            "net_bytes_sent": net_io.bytes_sent,
            "net_bytes_recv": net_io.bytes_recv,
            "net_packets_sent": net_io.packets_sent,
            "net_packets_recv": net_io.packets_recv,
            "process_count": proc_count,
        }

        top_procs = self._get_top_processes()
        sample["top_processes"] = top_procs

        return sample

    def _get_top_processes(self, count=5):
        """Identify the top processes by CPU and memory usage."""
        procs = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu_percent": info["cpu_percent"] or 0.0,
                    "memory_percent": round(info["memory_percent"] or 0.0, 2),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        procs.sort(key=lambda p: p["cpu_percent"], reverse=True)
        return procs[:count]

    def _print_sample(self, sample, iteration):
        """Print a formatted sample to stdout."""
        print(f"\n[Sample {iteration}] {sample['timestamp']}")
        print(f"  CPU: {sample['cpu_percent']:.1f}% | "
              f"Freq: {sample['cpu_freq_mhz']} MHz")
        print(f"  Memory: {sample['mem_used_mb']:.0f}MB / "
              f"{sample['mem_total_mb']:.0f}MB "
              f"({sample['mem_percent']:.1f}%)")
        print(f"  Swap: {sample['swap_used_mb']:.0f}MB / "
              f"{sample['swap_total_mb']:.0f}MB "
              f"({sample['swap_percent']:.1f}%)")
        print(f"  Disk: {sample['disk_used_gb']:.1f}GB / "
              f"{sample['disk_total_gb']:.1f}GB "
              f"({sample['disk_percent']:.1f}%)")
        print(f"  Network: TX={sample['net_bytes_sent']}, "
              f"RX={sample['net_bytes_recv']}")
        print(f"  Processes: {sample['process_count']}")
        if sample["top_processes"]:
            print("  Top processes by CPU:")
            for p in sample["top_processes"]:
                print(f"    [{p['pid']}] {p['name']} - "
                      f"CPU: {p['cpu_percent']:.1f}%, "
                      f"MEM: {p['memory_percent']:.1f}%")

    def generate_profile(self):
        """Generate a performance profile from collected samples."""
        if not self.samples:
            print("No samples collected. Run monitoring first.")
            return None

        profile = {
            "system_info": self._get_system_info(),
            "monitoring_config": {
                "interval": self.interval,
                "duration": self.duration,
                "total_samples": len(self.samples),
            },
            "cpu_profile": self._aggregate_cpu(),
            "memory_profile": self._aggregate_memory(),
            "disk_profile": self._aggregate_disk(),
            "network_profile": self._aggregate_network(),
            "process_profile": self._aggregate_processes(),
        }

        return profile

    def _get_system_info(self):
        """Collect static system information."""
        return {
            "hostname": platform.node(),
            "os": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "processor": platform.processor() or "unknown",
            "python_version": platform.python_version(),
            "cpu_physical": psutil.cpu_count(logical=False),
            "cpu_logical": psutil.cpu_count(logical=True),
            "total_memory_mb": round(
                psutil.virtual_memory().total / (1024 * 1024), 1
            ),
        }

    def _aggregate_cpu(self):
        """Compute CPU statistics from samples."""
        values = [s["cpu_percent"] for s in self.samples]
        return {
            "min": round(min(values), 1),
            "max": round(max(values), 1),
            "avg": round(sum(values) / len(values), 1),
            "samples": len(values),
        }

    def _aggregate_memory(self):
        """Compute memory statistics from samples."""
        values = [s["mem_percent"] for s in self.samples]
        used_values = [s["mem_used_mb"] for s in self.samples]
        return {
            "percent": {
                "min": round(min(values), 1),
                "max": round(max(values), 1),
                "avg": round(sum(values) / len(values), 1),
            },
            "used_mb": {
                "min": round(min(used_values), 1),
                "max": round(max(used_values), 1),
                "avg": round(sum(used_values) / len(used_values), 1),
            },
            "timeline": self.memory_timeline,
        }

    def _aggregate_disk(self):
        """Compute disk statistics from samples."""
        values = [s["disk_percent"] for s in self.samples]
        return {
            "min": round(min(values), 1),
            "max": round(max(values), 1),
            "avg": round(sum(values) / len(values), 1),
        }

    def _aggregate_network(self):
        """Compute network statistics from samples."""
        if len(self.samples) < 2:
            return {"note": "insufficient samples for network delta"}

        first = self.samples[0]
        last = self.samples[-1]
        elapsed = last["elapsed"] - first["elapsed"]

        bytes_sent_delta = last["net_bytes_sent"] - first["net_bytes_sent"]
        bytes_recv_delta = last["net_bytes_recv"] - first["net_bytes_recv"]

        return {
            "total_bytes_sent": bytes_sent_delta,
            "total_bytes_recv": bytes_recv_delta,
            "duration_seconds": round(elapsed, 2),
            "avg_send_bytes_per_sec": round(bytes_sent_delta / elapsed, 1) if elapsed > 0 else 0,
            "avg_recv_bytes_per_sec": round(bytes_recv_delta / elapsed, 1) if elapsed > 0 else 0,
        }

    def _aggregate_processes(self):
        """Aggregate process data across all samples."""
        all_proc_names = {}
        for sample in self.samples:
            for proc in sample.get("top_processes", []):
                name = proc["name"]
                if name not in all_proc_names:
                    all_proc_names[name] = []
                all_proc_names[name].append(proc["cpu_percent"])

        summary = []
        for name, cpus in all_proc_names.items():
            summary.append({
                "name": name,
                "avg_cpu": round(sum(cpus) / len(cpus), 1),
                "max_cpu": round(max(cpus), 1),
                "appearances": len(cpus),
            })

        summary.sort(key=lambda p: p["avg_cpu"], reverse=True)
        return summary[:10]

    def save_profile(self, profile, filepath):
        """Save the profile to a JSON file."""
        with open(filepath, "w") as fh:
            json.dump(profile, fh, indent=2, default=str)
        print(f"Profile saved to {filepath}")

    def print_profile_summary(self, profile):
        """Print a human-readable profile summary."""
        print("\n" + "=" * 60)
        print("  SYSTEM RESOURCE PROFILE SUMMARY")
        print("=" * 60)

        sys_info = profile["system_info"]
        print(f"\n  Host: {sys_info['hostname']}")
        print(f"  OS: {sys_info['os']}")
        print(f"  CPU: {sys_info['cpu_physical']} physical, "
              f"{sys_info['cpu_logical']} logical cores")
        print(f"  Total Memory: {sys_info['total_memory_mb']:.0f} MB")

        cpu = profile["cpu_profile"]
        print(f"\n  CPU Usage:")
        print(f"    Avg: {cpu['avg']}% | "
              f"Min: {cpu['min']}% | "
              f"Max: {cpu['max']}%")

        mem = profile["memory_profile"]
        print(f"\n  Memory Usage:")
        print(f"    Avg: {mem['percent']['avg']}% | "
              f"Min: {mem['percent']['min']}% | "
              f"Max: {mem['percent']['max']}%")
        print(f"    Avg Used: {mem['used_mb']['avg']:.0f} MB")

        net = profile["network_profile"]
        if "avg_send_bytes_per_sec" in net:
            print(f"\n  Network:")
            print(f"    Avg Send: {net['avg_send_bytes_per_sec']:.0f} B/s")
            print(f"    Avg Recv: {net['avg_recv_bytes_per_sec']:.0f} B/s")

        procs = profile["process_profile"]
        if procs:
            print(f"\n  Top Processes (by avg CPU):")
            for p in procs[:5]:
                print(f"    {p['name']:20s} avg={p['avg_cpu']:.1f}%  "
                      f"max={p['max_cpu']:.1f}%")

        print("\n" + "=" * 60)

    def print_memory_timeline(self):
        """Print a text-based visualization of memory usage over time."""
        if not self.memory_timeline:
            print("No memory timeline data available.")
            return

        timeline = self.memory_timeline
        max_mem = max(p["mem_used_mb"] for p in timeline)
        min_mem = min(p["mem_used_mb"] for p in timeline)
        mem_range = max_mem - min_mem if max_mem != min_mem else 1

        width = 40
        bar_char = "█"
        empty_char = "░"

        print("\n" + "=" * 72)
        print("  MEMORY USAGE OVER TIME")
        print("=" * 72)

        total_mb = self.samples[0]["mem_total_mb"] if self.samples else 0
        print(f"  Total Memory: {total_mb:.0f} MB")
        print(f"  Min Used: {min_mem:.0f} MB | Max Used: {max_mem:.0f} MB")
        print(f"  Range: {mem_range:.0f} MB")
        print("-" * 72)

        for entry in timeline:
            elapsed = entry["elapsed"]
            used = entry["mem_used_mb"]
            pct = entry["mem_percent"]
            fill = int(((used - min_mem) / mem_range) * width) if mem_range > 0 else width // 2

            bar = bar_char * max(1, fill) + empty_char * (width - max(1, fill))
            print(f"  {elapsed:6.1f}s | {used:7.0f} MB ({pct:5.1f}%) |{bar}|")

        print("-" * 72)
        print(f"  {'0s':<{width}} {max_mem:.0f} MB")
        print("=" * 72)

    def get_memory_timeline_json(self):
        """Return the memory timeline as a JSON-serializable list."""
        return self.memory_timeline

    def save_memory_timeline(self, filepath):
        """Save the memory timeline to a JSON file."""
        with open(filepath, "w") as fh:
            json.dump(self.memory_timeline, fh, indent=2)
        print(f"Memory timeline saved to {filepath}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="sys-resource-profiler: Monitor system resources "
                    "and generate performance profiles."
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=1.0,
        help="Sampling interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "-d", "--duration",
        type=float,
        default=10.0,
        help="Total monitoring duration in seconds (default: 10, 0=infinite)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path for the profile (JSON format)",
    )
    parser.add_argument(
        "--profile-only",
        action="store_true",
        help="Generate a quick 3-second profile and exit",
    )
    parser.add_argument(
        "--memory-timeline",
        action="store_true",
        help="Show memory usage over time after monitoring",
    )
    parser.add_argument(
        "--timeline-output",
        type=str,
        default=None,
        help="Output file path for memory timeline (JSON format)",
    )
    return parser.parse_args()


def main():
    """Entry point for sys-resource-profiler."""
    args = parse_args()

    if args.profile_only:
        args.duration = 3
        args.interval = 0.5

    profiler = ResourceProfiler(
        interval=args.interval,
        duration=args.duration,
        output_format=args.format,
        output_file=args.output,
    )

    profiler.start()
    profile = profiler.generate_profile()

    if profile:
        profiler.print_profile_summary(profile)

        if args.output:
            profiler.save_profile(profile, args.output)
        elif args.format == "json":
            print(json.dumps(profile, indent=2, default=str))

    if args.memory_timeline:
        profiler.print_memory_timeline()

        if args.timeline_output:
            profiler.save_memory_timeline(args.timeline_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
