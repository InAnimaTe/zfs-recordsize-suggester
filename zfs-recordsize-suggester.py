#!/usr/bin/env python3
import os
import sys
import math

def print_help():
    help_text = """
zfs-recordsize-suggester: Suggest an optimal ZFS recordsize for a dataset

Usage:
    zfs-recordsize-suggester.py [directory]

If [directory] is provided, the program scans that directory.
If no directory is provided, or if -h/--help is passed, this help menu is shown.

Output:
  1. File Size Breakdown: A table of file size buckets (with colors), file counts, and percentages.
  2. Wasted Space Analysis: For candidate recordsize values (from 8K up to 16M), the program simulates ZFS allocation,
     calculates total wasted space and overhead (unused allocation percentage). The candidate with the lowest overhead is highlighted.
  3. Statistics: Total files, directories, average and median file sizes.
  4. Final Recommendation: Based on a "mode candidate" computed by accumulating the most frequent buckets until at least 50%
     of the files are reached and the wasted space candidate, the program recommends a ZFS recordsize.

Notes:
  - The mode candidate is determined by taking the upper limit candidate of the buckets that together contain ≥50% of the files.
  - The wasted space analysis simulates ZFS’s block allocation: files larger than a candidate are allocated in multiples of that candidate;
    for smaller files, the allocation is the smallest power-of-two (minimum 512B) that is at least the file size but not exceeding the candidate.
  - The final recommendation is the maximum (in bytes) of the mode candidate and the wasted-space candidate.
  - This tool supports candidate recordsize values up to 16M (assuming your ZFS pool is configured with large_blocks enabled).

Examples:
    zfs-recordsize-suggester.py /path/to/directory
    zfs-recordsize-suggester.py -h
"""
    print(help_text)

def bucket_for_size(size):
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
    total_size = 0
    file_sizes = []
    dir_count = 0
    for root, dirs, files in os.walk(directory):
        dir_count += len(dirs)
        for file in files:
            try:
                path = os.path.join(root, file)
                size = os.stat(path).st_size
                total_size += size
                file_sizes.append(size)
                bucket = bucket_for_size(size)
                counts[bucket] = counts.get(bucket, 0) + 1
                total += 1
            except Exception:
                pass
    return counts, total, total_size, file_sizes, dir_count

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0
    return f"{size:.{decimal_places}f} P"

def compute_median(sizes):
    if not sizes:
        return 0
    sizes_sorted = sorted(sizes)
    n = len(sizes_sorted)
    if n % 2 == 1:
        return sizes_sorted[n//2]
    else:
        return (sizes_sorted[n//2 - 1] + sizes_sorted[n//2]) / 2

def get_mode_bucket(counts):
    if not counts:
        return None
    return max(counts, key=counts.get)

def size_to_bytes(size_str):
    mapping = {
        "8K": 8 * 1024,
        "16K": 16 * 1024,
        "32K": 32 * 1024,
        "64K": 64 * 1024,
        "128K": 128 * 1024,
        "256K": 256 * 1024,
        "512K": 512 * 1024,
        "1M": 1024 * 1024,
        "2M": 2 * 1024 * 1024,
        "4M": 4 * 1024 * 1024,
        "8M": 8 * 1024 * 1024,
        "16M": 16 * 1024 * 1024,
    }
    return mapping.get(size_str, 0)

def bytes_to_size(rec_bytes):
    if rec_bytes <= 16 * 1024:
        return "16K"
    elif rec_bytes <= 32 * 1024:
        return "32K"
    elif rec_bytes <= 64 * 1024:
        return "64K"
    elif rec_bytes <= 128 * 1024:
        return "128K"
    elif rec_bytes <= 256 * 1024:
        return "256K"
    elif rec_bytes <= 512 * 1024:
        return "512K"
    elif rec_bytes <= 1024 * 1024:
        return "1M"
    elif rec_bytes <= 2 * 1024 * 1024:
        return "2M"
    elif rec_bytes <= 4 * 1024 * 1024:
        return "4M"
    elif rec_bytes <= 8 * 1024 * 1024:
        return "8M"
    else:
        return "16M"

def simulate_zfs_allocation(file_size, candidate_bytes):
    if file_size == 0:
        return 0
    if file_size >= candidate_bytes:
        blocks = (file_size + candidate_bytes - 1) // candidate_bytes
        return blocks * candidate_bytes
    else:
        alloc = 512
        while alloc < file_size and alloc < candidate_bytes:
            alloc *= 2
        return alloc

def compute_waste(candidate_bytes, file_sizes):
    total_waste = 0
    total_allocated = 0
    for s in file_sizes:
        allocated = simulate_zfs_allocation(s, candidate_bytes)
        total_waste += allocated - s
        total_allocated += allocated
    return total_waste, total_allocated

def print_table(counts, total):
    data = []
    for bucket, count in counts.items():
        perc = (count / total) * 100 if total > 0 else 0
        data.append((bucket, count, perc))
    data.sort(key=lambda x: x[2], reverse=True)

    col1 = 24  # Reduced "File Sizes" column width
    col2 = 11
    col3 = 11

    buckets_order = [
        "<1K", "1K–2K", "2K–4K", "4K–8K", "8K–16K", "16K–32K",
        "32K–64K", "64K–128K", "128K–256K", "256K–512K",
        "512K–1M", "1M–2M", "2M–4M", "4M–8M", "8M–16M", ">16M"
    ]
    colors = [
        "\033[31m", "\033[32m", "\033[33m", "\033[34m",
        "\033[35m", "\033[36m", "\033[91m", "\033[92m",
        "\033[93m", "\033[94m", "\033[95m", "\033[96m",
        "\033[37m", "\033[90m", "\033[38;5;208m", "\033[38;5;141m"
    ]
    bucket_color_map = {bucket: colors[i % len(colors)] for i, bucket in enumerate(buckets_order)}

    reset = "\033[0m"
    separator = f"+{'-'*(col1+2)}+{'-'*(col2+2)}+{'-'*(col3+2)}+"
    header = f"| {'File Sizes'.ljust(col1)} | {'Files'.rjust(col2)} | {'Percent ↓'.rjust(col3)} |"

    print("\nFile Size Breakdown:")
    print(separator)
    print(header)
    print(separator)
    for bucket, count, perc in data:
        perc_str = f"{perc:.2f}%".rjust(col3)
        bucket_padded = bucket.ljust(col1)
        bucket_color = bucket_color_map.get(bucket, "")
        bucket_colored = f"{bucket_color}{bucket_padded}{reset}"
        row = f"| {bucket_colored} | {str(count).rjust(col2)} | {perc_str} |"
        print(row)
    print(separator)

def compute_mode_candidate(counts, total):
    mapping_mode = {
        "<1K": "8K",
        "1K–2K": "8K",
        "2K–4K": "8K",
        "4K–8K": "8K",
        "8K–16K": "16K",
        "16K–32K": "16K",
        "32K–64K": "32K",
        "64K–128K": "64K",
        "128K–256K": "128K",
        "256K–512K": "256K",
        "512K–1M": "512K",
        "1M–2M": "1M",
        "2M–4M": "1M",
        "4M–8M": "1M",
        "8M–16M": "1M",
        ">16M": "1M"
    }
    bucket_list = [(bucket, count) for bucket, count in counts.items()]
    bucket_list.sort(key=lambda x: x[1], reverse=True)
    cumulative = 0
    selected = []
    for bucket, count in bucket_list:
        cumulative += count
        candidate = mapping_mode.get(bucket, "128K")
        selected.append((bucket, candidate, count))
        if cumulative >= total * 0.5:
            break
    best_candidate = max([cand for _, cand, _ in selected], key=lambda x: size_to_bytes(x))
    return best_candidate, selected

def candidate_to_bucket(candidate):
    if candidate.endswith("K"):
        num = int(candidate[:-1])
        return f"{candidate}–{num*2}K"
    elif candidate.endswith("M"):
        num = int(candidate[:-1])
        return f"{candidate}–{num*2}M"
    else:
        return candidate

def compute_best_candidate(file_sizes):
    candidates = ["8K", "16K", "32K", "64K", "128K", "256K", "512K", "1M", "2M", "4M", "8M", "16M"]
    best = None
    best_overhead = float('inf')
    candidate_data = []
    for candidate in candidates:
        candidate_bytes = size_to_bytes(candidate)
        waste, allocated = compute_waste(candidate_bytes, file_sizes)
        overhead = (waste / allocated * 100) if allocated > 0 else float('inf')
        candidate_data.append((candidate, waste, overhead))
        if overhead < best_overhead:
            best = candidate
            best_overhead = overhead
    return best, best_overhead, candidate_data

def print_waste_table(file_sizes, candidate_data):
    col1 = 10  # Candidate column width
    col2 = 20  # Total wasted column width
    col3 = 12  # Overhead column width
    separator = f"+{'-'*(col1+2)}+{'-'*(col2+2)}+{'-'*(col3+2)}+"
    header = f"| {'Candidate'.center(col1)} | {'Total Wasted'.center(col2)} | {'Overhead ↑'.center(col3)} |"

    buckets_order = [
        "<1K", "1K–2K", "2K–4K", "4K–8K", "8K–16K", "16K–32K",
        "32K–64K", "64K–128K", "128K–256K", "256K–512K",
        "512K–1M", "1M–2M", "2M–4M", "4M–8M", "8M–16M", ">16M"
    ]
    colors = [
        "\033[31m", "\033[32m", "\033[33m", "\033[34m",
        "\033[35m", "\033[36m", "\033[91m", "\033[92m",
        "\033[93m", "\033[94m", "\033[95m", "\033[96m",
        "\033[37m", "\033[90m", "\033[38;5;208m", "\033[38;5;141m"
    ]
    bucket_color_map = {bucket: colors[i % len(colors)] for i, bucket in enumerate(buckets_order)}
    reset = "\033[0m"

    print("\nWasted Space Analysis:")
    print(separator)
    print(header)
    print(separator)
    min_overhead = min(candidate_data, key=lambda x: x[2])[2] if candidate_data else None
    for candidate, waste, overhead in candidate_data:
        candidate_bucket = candidate_to_bucket(candidate)
        candidate_color = bucket_color_map.get(candidate_bucket, "")
        candidate_colored = f"{candidate_color}{candidate.center(col1)}{reset}"
        waste_hr = human_readable_size(waste)
        overhead_str = f"{overhead:.2f}%".rjust(col3)
        if math.isclose(overhead, min_overhead, rel_tol=1e-6):
            overhead_str = f"\033[32m{overhead_str}{reset}"
        row = f"| {candidate_colored} | {waste_hr.center(col2)} | {overhead_str} |"
        print(row)
    print(separator)

def compute_final_recommendation(counts, candidate_data):
    mode_candidate, mode_details = compute_mode_candidate(counts, total_files)
    print("\nMode Candidate Details (Buckets considered until reaching 50% of files):")
    cumulative = 0
    for bucket, candidate, count in mode_details:
        cumulative += count
        print(f"  Bucket: {bucket} -> Candidate: {candidate} ({count} files)")
    print(f"Total files in selected buckets: {cumulative} (>= 50% of total files)")

    best_candidate, best_overhead, _ = min(candidate_data, key=lambda x: x[2])
    final_bytes = max(size_to_bytes(mode_candidate), size_to_bytes(best_candidate))
    return bytes_to_size(final_bytes), mode_candidate, best_candidate

# Global variable to hold total file count.
total_files = 0

def main():
    global total_files
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)
    directory = sys.argv[1]
    print(f"Scanning directory: {directory}\n")
    counts, total, total_size, file_sizes, dir_count = scan_directory(directory)
    total_files = total
    if total == 0:
        print("No files found.")
    else:
        print_table(counts, total)
        best_candidate, best_overhead, candidate_data = compute_best_candidate(file_sizes)
        print_waste_table(file_sizes, candidate_data)
        mode_candidate, _ = compute_mode_candidate(counts, total)
        final_rec, mode_rec, waste_rec = compute_final_recommendation(counts, candidate_data)
        avg = total_size / total
        median = compute_median(file_sizes)
        hr_avg = human_readable_size(avg)
        hr_med = human_readable_size(median)

        print("\nStatistics:")
        print(f"Total files: {total}")
        print(f"Total directories: {dir_count}")
        print(f"Average file size: {hr_avg}")
        print(f"Median file size:  {hr_med}")

        print("\nRecommendation:")
        print(f"Mode candidate (50% accumulation) is: {mode_candidate}")
        print(f"Wasted space candidate (lowest overhead) is: {best_candidate}")
        print("Final recommended ZFS recordsize for a dataset like this is:")
        box_width = 40
        rec_text = f" {final_rec} "
        box_line = "+" + "-"*(box_width-2) + "+"
        print("\033[32m" + box_line)
        print("|" + rec_text.center(box_width-2) + "|")
        print(box_line + "\033[0m")
        print("\nExplanation:")
        print("  - Mode candidate: determined by accumulating buckets (sorted by frequency) until reaching 50% of files,")
        print("    then choosing the candidate (upper limit) of the highest bucket in that selection.")
        print("  - Wasted space candidate: the recordsize candidate that minimizes wasted space overhead (simulated allocation).")
        print("  The final recommendation is the larger (in bytes) of these two.")

if __name__ == "__main__":
    main()
