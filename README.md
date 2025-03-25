# zfs-recordsize-suggester

**zfs-recordsize-suggester** is a Python tool designed to analyze the file size distribution in a given directory and suggest an optimal ZFS recordsize for a dataset containing similar data. The tool takes into account several factors:

1. **File Size Breakdown:**  
   The program groups files into predefined size buckets (e.g., `<1K`, `1K–2K`, `4K–8K`, etc.) and displays a table showing the number and percentage of files in each bucket. This helps you understand the typical file size distribution in your dataset.

2. **Wasted Space Analysis:**  
   The tool simulates ZFS block allocation for various candidate recordsize values (from 8K up to 16M, assuming large block support is enabled). For each candidate, it calculates the total "wasted" space (i.e., the difference between allocated space and the actual file size) and the overhead percentage. The candidate with the lowest overhead is highlighted.

3. **Mode Candidate (50% Accumulation):**  
   Instead of simply using the most frequent bucket, the tool accumulates the buckets (sorted by file count) until the cumulative count reaches at least 50% of the total files. It then selects the candidate recordsize corresponding to the upper limit of the highest bucket in that 50% subset.

4. **Final Recommendation:**  
   The final recommended recordsize is determined by comparing:
   - The candidate from the mode-based calculation (covering 50% of the files) and
   - The candidate from the wasted space analysis (with the lowest overhead).  
   The recommendation is the one with the larger byte value, ensuring that larger files incur less waste.

## Important Resources on ZFS Recordsize

Please consider reviewing these great articles on how ZFS handles `recordsize` for Datasets!

* [Klara Systems - Tuning Recordsize in OpenZFS](https://klarasystems.com/articles/tuning-recordsize-in-openzfs/#:~:text=The%20recordsize%20property%20sets%20the%20maximum)
* [High-Availability - ZFS Tuning Guide](https://www.high-availability.com/docs/ZFS-Tuning-Guide/#:~:text=ZFS%20on%20linux%20provides%20an,time%20the%20file%20is%20accessed)
* [OpenZFS Official Docs - Performance Tuning](https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Workload%20Tuning.html)


## How to Run

Ensure you have Python 3 installed. You can run the tool from the command line as follows:

```bash
./zfs-recordsize-suggester.py [directory]
```

*	If you specify a directory, the tool will scan that directory.
*	If no directory is specified or if you pass -h or --help, a help menu is displayed.

### Output

The program outputs four main sections:
	1.	File Size Breakdown:
A table showing file size buckets (with a reduced “File Sizes” column), the number of files in each bucket, and the percentage of the total.
	2.	Wasted Space Analysis:
A table displaying candidate recordsize values (from 8K up to 16M) along with the simulated total wasted space and overhead percentage. The header for Overhead includes an up arrow (↑) to indicate that lower overhead is better. The candidate with the lowest overhead is highlighted in green.
	3.	Statistics:
Displays the total number of files and directories, as well as the average and median file sizes (in human‑readable format).
	4.	Final Recommendation:
The tool prints detailed mode candidate calculations (i.e., which buckets were considered to cover 50% of the files) and then shows the final recommended ZFS recordsize in a green box.

## Calculation Logic

*	File Size Breakdown:
	* Files are grouped into buckets based on their size (e.g., <1K, 1K–2K, 4K–8K, etc.). The tool counts files in each bucket and calculates the percentage of the total.

*	Wasted Space Simulation:

	For each candidate recordsize:

	* For files larger than or equal to the candidate, ZFS is simulated to allocate space in multiples of that candidate.
		* For files smaller than the candidate, ZFS is simulated to allocate a block that is the smallest power-of-two (with a minimum of 512 B) that is at least the file’s size but not exceeding the candidate.
		* The tool sums the wasted space (allocated minus actual file size) over all files and computes the overhead percentage.

*	Mode Candidate (50% Accumulation):
	* Buckets are sorted by frequency. The tool accumulates the file counts from the most frequent buckets until at least 50% of the files are covered. Among these buckets, it selects the candidate recordsize corresponding to the highest upper-limit (e.g., if buckets 4K–8K and 8K–16K cover 50%, the mode candidate becomes 16K).

*	Final Recommendation:
	* The final recommendation is the candidate with the larger byte value between the mode candidate (from 50% accumulation) and the candidate with the lowest overhead from the wasted space analysis. This approach ensures that larger files, which might otherwise cause significant waste, are accommodated.

## Caveats

*	Simplified Model:
	* The simulation of ZFS block allocation is a simplified approximation and may not exactly reflect ZFS’s internal behavior.

*	Large Block Sizes:
	* This tool supports candidate recordsize values up to 16M. To use such large recordsize values in practice, your ZFS pool must be configured with large_blocks enabled.

*	Workload Specificity:
	* The recommendation is based solely on file size distribution and simulated allocation. Actual optimal performance may also depend on I/O patterns and other workload characteristics.

### Note on ZFS Recordsize Behavior

ZFS’s recordsize property sets the maximum block size that can be allocated for data in a dataset. This means that:

*	For large files:
	* ZFS writes data in blocks that are up to the recordsize value. If a file’s size exceeds the recordsize, ZFS will split the file into multiple blocks, each up to the maximum size.
*	For small files:
	* ZFS does not waste space by always allocating the full recordsize. Instead, it allocates a smaller block that is closer to the actual file size—typically the smallest power-of-two (with a minimum of 512 B) that is large enough to hold the file. This minimizes wasted space.

In our tool, we’ve incorporated this behavior into the wasted space analysis. When simulating ZFS allocation, for files smaller than a candidate recordsize, we calculate the allocated size as the smallest power-of-two (not exceeding the candidate) that can accommodate the file. For larger files, we assume that space is allocated in multiples of the candidate recordsize. This model helps ensure that the recommended recordsize minimizes wasted space across your dataset, especially when there is a mix of small and large files.

## Example Output

```
└[~]> ~/zfs-recordsize-suggester/zfs-recordsize-suggester.py ~/
Scanning directory: /Users/mario/


File Size Breakdown:
+--------------------------+-------------+-------------+
| File Sizes               |       Files |   Percent ↓ |
+--------------------------+-------------+-------------+
| 4K–8K                    |       50166 |      24.81% |
| <1K                      |       45039 |      22.27% |
| 8K–16K                   |       30520 |      15.09% |
| 2K–4K                    |       22805 |      11.28% |
| 1K–2K                    |       16503 |       8.16% |
| 16K–32K                  |       11118 |       5.50% |
| 32K–64K                  |        7557 |       3.74% |
| 64K–128K                 |        5629 |       2.78% |
| 128K–256K                |        2968 |       1.47% |
| 512K–1M                  |        2779 |       1.37% |
| 256K–512K                |        2326 |       1.15% |
| 1M–2M                    |        1912 |       0.95% |
| 2M–4M                    |        1484 |       0.73% |
| 4M–8M                    |         683 |       0.34% |
| >16M                     |         411 |       0.20% |
| 8M–16M                   |         335 |       0.17% |
+--------------------------+-------------+-------------+

Wasted Space Analysis:
+------------+----------------------+--------------+
| Candidate  |     Total Wasted     |  Overhead ↑  |
+------------+----------------------+--------------+
|     8K     |      453.03 MiB      |        0.46% |
|    16K     |      616.00 MiB      |        0.62% |
|    32K     |      847.08 MiB      |        0.86% |
|    64K     |       1.13 GiB       |        1.17% |
|    128K    |       1.58 GiB       |        1.62% |
|    256K    |       2.28 GiB       |        2.33% |
|    512K    |       3.36 GiB       |        3.39% |
|     1M     |       4.75 GiB       |        4.73% |
|     2M     |       6.50 GiB       |        6.36% |
|     4M     |       8.24 GiB       |        7.93% |
|     8M     |      10.10 GiB       |        9.55% |
|    16M     |      12.24 GiB       |       11.34% |
+------------+----------------------+--------------+

Mode Candidate Details (Buckets considered until reaching 50% of files):
  Bucket: 4K–8K -> Candidate: 8K (50166 files)
  Bucket: <1K -> Candidate: 8K (45039 files)
  Bucket: 8K–16K -> Candidate: 16K (30520 files)
Total files in selected buckets: 125725 (>= 50% of total files)

Statistics:
Total files: 202235
Total directories: 50394
Total Dataset Scanned Size: 95.71 GiB (base 2) / 102.77 GB (base 10) / 822.17 Gb
Average file size: 496.27 KiB
Median file size:  4.82 KiB

Recommendation:
Mode candidate (50% accumulation) is: 16K
Wasted space candidate (lowest overhead) is: 8K
Final recommended ZFS recordsize for a dataset like this is:
+--------------------------------------+
|                 16K                  |
+--------------------------------------+

Explanation:
  - Mode candidate: determined by accumulating buckets (sorted by frequency) until reaching 50% of files,
    then choosing the candidate (upper limit) of the highest bucket in that selection.
  - Wasted space candidate: the recordsize candidate that minimizes wasted space overhead (simulated allocation).
  The final recommendation is the larger (in bytes) of these two.
```

## License

This project is licensed under the MIT License.

Feel free to adjust the content as needed for your GitHub repository!
