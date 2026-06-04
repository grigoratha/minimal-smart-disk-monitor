import json
import math

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import datetime, timedelta

def round_down_5(x):
    return math.floor(x / 5) * 5

def round_up_5(x):
    return math.ceil(x / 5) * 5

def load_data(path="data/archive.json", days=30):
    with open(path, "r") as f:
        data = json.load(f)

    cutoff = datetime.now() - timedelta(days=days)

    devices = {}
    all_temps = []

    for entry in data:
        ts = datetime.fromisoformat(entry["timestamp"])

        if ts < cutoff:
            continue

        for dev_id, info in entry["devices"].items():
            if dev_id not in devices:
                devices[dev_id] = {
                    "timestamps": [],
                    "health": [],
                    "temp": [],
                    "model": info["model_name"]
                }

            devices[dev_id]["timestamps"].append(ts)
            devices[dev_id]["health"].append(info["health"])
            devices[dev_id]["temp"].append(info["temperature"])

            all_temps.append(info["temperature"])

    return devices, all_temps

def plot_health(devices, n, rows, cols, fig, gs):
    device_list = list(devices.items())

    for i, (dev_id, d) in enumerate(device_list):
        r = i // cols
        c = i % cols

        ax = fig.add_subplot(gs[r, c])

        x = d["timestamps"]
        y = d["health"]

        y_min = round_down_5(min(y) - 5)
        y_max = round_up_5(max(y) + 5)

        ax.plot(x, y, marker="o", linewidth=2)

        ax.set_title(d["model"], fontsize=9)
        ax.set_ylim(y_min, y_max)

        ax.axhline(100, color="gray", linestyle="--", linewidth=1)
        ax.grid(True, alpha=0.3)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))
        plt.setp(ax.get_xticklabels(), fontsize=7)

    # hide empty slots
    for j in range(n, rows * cols):
        ax = fig.add_subplot(gs[j // cols, j % cols])
        ax.axis("off")

def plot_temperature(devices, all_temps, rows, cols, fig, gs):
    ax_temp = fig.add_subplot(gs[rows, :])

    offset_step = 12  # visual separation

    for i, (dev_id, d) in enumerate(devices.items()):
        offset = i * offset_step

        shifted_temp = [t + offset for t in d["temp"]]

        ax_temp.plot(
            d["timestamps"],
            shifted_temp,
            marker="o",
            linewidth=2,
            label=f"{d['model']} (+{offset}°C)"
            
        )

    ax_temp.set_title("Disk Temperature")
    ax_temp.set_ylabel("Temperature (°C)")
    ax_temp.set_xlabel("Time")

    temp_max = max(all_temps) + 5
    ax_temp.set_ylim(0, temp_max)

    ax_temp.yaxis.set_major_locator(ticker.MultipleLocator(10))

    ax_temp.grid(True, alpha=0.3)
    ax_temp.legend(loc="lower left", fontsize=8)

    ax_temp.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))
    plt.setp(ax_temp.get_xticklabels(), fontsize=8)


def plot_dashboard(devices, all_temps):
    device_list = list(devices.items())
    n = len(device_list)

    cols = 3
    rows = math.ceil(n / cols)

    fig = plt.figure(figsize=(15, 1.2 * rows + 6))
    gs = fig.add_gridspec(rows + 1, cols)

    plot_health(devices, n, rows, cols, fig, gs)
    plot_temperature(devices, all_temps, rows, cols, fig, gs)

    plt.tight_layout()
    plt.show()

def run_dashboard(days=30):
    devices, all_temps = load_data(days=days)
    plot_dashboard(devices, all_temps)