#!/usr/bin/env python3

import argparse
import os
import re
import sys

# Needed to include from ../client/*.py
PARENT = os.path.join(os.path.dirname(__file__), os.path.pardir)
sys.path.append(os.path.abspath(os.path.join(PARENT, 'client')))

from bench_engine import bench_engine

if __name__ == '__main__':

    p = argparse.ArgumentParser()
    p.add_argument('--seconds', type=int, default=10)
    p.add_argument('--threads', type=int, default=1)
    p.add_argument('--regex'  , type=str, default=None)
    args = p.parse_args()

    for name in sorted(os.listdir('tarballs')):

        image_name = name.removesuffix('.tar.zst')
        if args.regex and not re.search(args.regex, image_name):
            continue

        nps_values, endtimes, peak_kb = bench_engine(image_name, args.threads, args.seconds, args.seconds * 3)

        avg_nps    = sum(nps_values) / len(nps_values)
        max_spread = 100.0 * (max(nps_values) - min(nps_values)) / avg_nps
        max_delta  = (max(endtimes) - min(endtimes))
        peak_mb    = peak_kb / 1024
        print ('%-40s %8d nps %5.2f%% %.3fs %8.1f MB' % (image_name, avg_nps, max_spread, max_delta, peak_mb))
