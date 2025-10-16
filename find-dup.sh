#!/usr/bin/env python3
import sys, re, collections

# Use file_path instead of file_name to detect TRUE duplicates (same path processed multiple times)
pattern = re.compile(r'"file_path"\s*:\s*"([^"]+)"')
counts = collections.Counter()

for line in sys.stdin:
    m = pattern.search(line)
    if m:
        counts[m.group(1)] += 1

# Only show actual duplicates (count > 1)
duplicates = [(path, count) for path, count in counts.items() if count > 1]

if duplicates:
    print("🚨 DUPLICATES FOUND (same path tagged multiple times):")
    print()
    for path, count in sorted(duplicates, key=lambda x: x[1], reverse=True):
        print(f"{count:4}  {path}")
    print()
    print(f"Total duplicates: {len(duplicates)}")
else:
    print("✅ NO DUPLICATES! Each unique file path tagged exactly once.")
    print(f"Total unique files processed: {len(counts)}")

