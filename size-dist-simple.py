#!/usr/bin/env python3
import os
import sys

def bucket_for_size(size):
    # Return bucket labels based on explicit range comparisons.
    if size < 1024:
        return "<1K"
    elif 1024 <= size < 2048:
        return "1K–2K"
    elif 2048 <= size < 4096:
        return "2K–4K"
    elif 4096 <= size < 8192:
        return "4K–8K"
    elif 8192 <= size < 16384:
        return "8K–16K"
    elif 16384 <= size < 32768:
        return "16K–32K"
    elif 32768 <= size < 65536:
        return "32K–64K"
    elif 65536 <= size < 131072:
        return "64K–128K"
    elif 131072 <= size < 262144:
        return "128K–256K"
    elif 262144 <= size < 524288:
        return "256K–512K"
    elif 524288 <= size < 1048576:
        return "512K–1M"
    elif 1048576 <= size < 2097152:
        return "1M–2M"
    elif 2097152 <= size < 4194304:
        return "2M–4M"
    elif 4194304 <= size < 8388608:
        return "4M–8M"
    elif 8388608 <= size < 16777216:
        return "8M–16M"
    else:
        return ">16M"

def scan_directory(directory):
    counts = {}
    total = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            try:
                path = os.path.join(root, file)
                size = os.stat(path).st_size
                bucket = bucket_for_size(size)
                counts[bucket] = counts.get(bucket, 0) + 1
                total += 1
            except Exception:
                # Skip files that cause errors.
                pass
    return counts, total

def print_table(counts, total):
    # Build data as a list of tuples: (bucket, count, percentage)
    data = []
    for bucket, count in counts.items():
        perc = (count / total) * 100 if total > 0 else 0
        data.append((bucket, count, perc))
    # Sort by percentage in descending order.
    data.sort(key=lambda x: x[2], reverse=True)
    
    # Define fixed column widths.
    col1 = 30  # Record Sizes column width
    col2 = 11  # Files column width
    col3 = 11  # Percent column width (includes "%" symbol)
    
    # Define bucket order (from smallest to largest) so we assign consistent colors.
    buckets_order = [
        "<1K", "1K–2K", "2K–4K", "4K–8K", "8K–16K",
        "16K–32K", "32K–64K", "64K–128K", "128K–256K",
        "256K–512K", "512K–1M", "1M–2M", "2M–4M", "4M–8M",
        "8M–16M", ">16M"
    ]
    # Define a list of ANSI color codes. (Cycle if more buckets than colors.)
    colors = [
        "\033[31m",  # Red
        "\033[32m",  # Green
        "\033[33m",  # Yellow
        "\033[34m",  # Blue
        "\033[35m",  # Magenta
        "\033[36m",  # Cyan
        "\033[91m",  # Bright Red
        "\033[92m",  # Bright Green
        "\033[93m",  # Bright Yellow
        "\033[94m",  # Bright Blue
        "\033[95m",  # Bright Magenta
        "\033[96m",  # Bright Cyan
        "\033[37m",  # White
        "\033[90m",  # Gray
        "\033[38;5;208m",  # Orange (if supported)
        "\033[38;5;141m",  # Violet (if supported)
    ]
    # Create a dictionary mapping bucket label to a color code.
    bucket_color_map = {}
    for i, bucket in enumerate(buckets_order):
        bucket_color_map[bucket] = colors[i % len(colors)]
    
    # ANSI reset code.
    reset = "\033[0m"
    
    # Build the separator and header lines.
    separator = f"+{'-' * (col1 + 2)}+{'-' * (col2 + 2)}+{'-' * (col3 + 2)}+"
    header = f"| {'Record Sizes'.ljust(col1)} | {'Files'.rjust(col2)} | {'Percent'.rjust(col3)} |"
    
    print(separator)
    print(header)
    print(separator)
    
    # Print each row.
    for bucket, count, perc in data:
        # Create the percent string with a trailing "%" and right-justify it.
        perc_str = f"{perc:.2f}%".rjust(col3)
        # Pad the bucket field.
        bucket_padded = bucket.ljust(col1)
        # Get the color for this bucket; default to no color if not defined.
        bucket_color = bucket_color_map.get(bucket, "")
        bucket_colored = f"{bucket_color}{bucket_padded}{reset}"
        row = f"| {bucket_colored} | {str(count).rjust(col2)} | {perc_str} |"
        print(row)
    
    print(separator)

def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"Scanning directory: {directory}\n")
    counts, total = scan_directory(directory)
    if total == 0:
        print("No files found.")
    else:
        print_table(counts, total)

if __name__ == "__main__":
    main()