# sys-resource-profiler

Lightweight tool for monitoring system resource usage and generating performance profiles.

## Features

- Real-time monitoring of CPU, memory, swap, disk, and network usage
- Top process identification by CPU and memory consumption
- Configurable sampling interval and monitoring duration
- Performance profile generation with aggregated statistics (min, max, avg)
- Output in human-readable text or machine-readable JSON
- Graceful shutdown via Ctrl+C
- Cross-platform support (Linux, macOS, Windows)

## Requirements

- Python 3.6+
- psutil

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic monitoring (10 seconds, 1-second interval)

```bash
python sys_resource_profiler.py
```

### Custom interval and duration

```bash
python sys_resource_profiler.py -i 2 -d 30
```

Monitor every 2 seconds for 30 seconds.

### Quick profile

```bash
python sys_resource_profiler.py --profile-only
```

Runs a quick 3-second monitoring session and prints the summary.

### JSON output

```bash
python sys_resource_profiler.py -f json -d 5 > profile.json
```

### Save profile to file

```bash
python sys_resource_profiler.py -d 15 -o my_profile.json
```

Monitors for 15 seconds and saves the full profile as JSON.

### Run indefinitely (stop with Ctrl+C)

```bash
python sys_resource_profiler.py -d 0
```

## Command-Line Options

| Flag             | Description                              | Default |
|------------------|------------------------------------------|---------|
| `-i`, `--interval`  | Sampling interval in seconds             | 1.0     |
| `-d`, `--duration`  | Total monitoring duration (0 = infinite) | 10      |
| `-f`, `--format`    | Output format (`text` or `json`)         | text    |
| `-o`, `--output`    | Output file path for JSON profile        | None    |
| `--profile-only`    | Quick 3-second profile and exit          | False   |

## Output

The tool produces two kinds of output:

1. **Live monitoring data** — printed at each sampling interval, showing current resource usage and top processes.
2. **Profile summary** — aggregated statistics computed after monitoring stops, including min/max/avg for each metric.

## License

MIT
