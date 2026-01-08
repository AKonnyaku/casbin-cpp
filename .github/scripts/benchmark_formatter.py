import json
import math
import os
import platform
import sys

def fmt_ns(ns):
    if ns < 0 or math.isnan(ns): return "-"
    if ns < 1000: return f"{ns:.2f}n"
    if ns < 1e6: return f"{ns/1e3:.2f}µ"
    if ns < 1e9: return f"{ns/1e6:.2f}m"
    return f"{ns/1e9:.2f}"

def load_results(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {b["name"]: b for b in data.get("benchmarks", [])}
    except Exception as e:
        print(f"Error loading {path}: {e}", file=sys.stderr)
        return {}

def main():
    if not os.path.exists("base-bench.json") or not os.path.exists("pr-bench.json"):
        print("Benchmark files not found.", file=sys.stderr)
        return

    base = load_results("base-bench.json")
    pr = load_results("pr-bench.json")
    all_keys = sorted(list(set(base.keys()) | set(pr.keys())))

    # Get CPU info
    cpu_info = "Unknown CPU"
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_info = line.split(":", 1)[1].strip()
                        break
    except: pass

    # Append to comparison.md if it exists, otherwise print to stdout
    output_file = "comparison.md"
    
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"goos: {platform.system().lower()}\n")
        f.write(f"goarch: {platform.machine().lower()}\n")
        f.write(f"pkg: casbin-cpp\n")
        f.write(f"cpu: {cpu_info}\n")
        f.write("\n")
        
        # Table Headers
        # Col 1: 50 chars
        # Col 2: 19 chars
        # Col 3: 19 chars
        # Col 4: 25 chars (stats)
        # Col 5: Delta
        
        f.write(f"{'':<50} │ {'base-bench.json':^19} │ {'pr-bench.json':^47} │\n")
        f.write(f"{'':<50} │ {'sec/op':^19} │ {'sec/op':^19} {'vs base':<27} │   Delta\n")

        base_vals = []
        pr_vals = []

        for k in all_keys:
            b_item = base.get(k)
            p_item = pr.get(k)
            b_val = b_item.get("cpu_time", 0.0) if b_item else 0.0
            p_val = p_item.get("cpu_time", 0.0) if p_item else 0.0
            
            if b_val > 0: base_vals.append(b_val)
            if p_val > 0: pr_vals.append(p_val)
            
            if b_val > 0:
                diff = (p_val - b_val) / b_val
                diff_str = f"{diff:+.2%}"
                if diff < -0.10: status = "🚀"
                elif diff > 0.10: status = "🐌"
                else: status = "➡️"
            else:
                diff_str = "-"
                status = ""
            
            b_str = (fmt_ns(b_val) + " ± ∞ ¹") if b_val else "-"
            p_str = (fmt_ns(p_val) + " ± ∞ ¹") if p_val else "-"
            
            stats = "~ (p=1.000 n=1) ²"
            
            display_name = k.replace("Benchmark", "")
            
            # Data row alignment
            # Use 3 spaces to mimic ' │ ' position
            if b_val > 0 and p_val > 0:
                 f.write(f"{display_name:<50}   {b_str:>19}   {p_str:>19}   {stats:<27}   {diff_str:>9} {status}\n")
            else:
                 f.write(f"{display_name:<50}   {b_str:>19}   {p_str:>19}   {'':<27}   {diff_str:>9} {status}\n")

if __name__ == "__main__":
    main()
