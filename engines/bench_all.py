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
    p.add_argument('--seconds' , type=int, default=10)
    p.add_argument('--threads' , type=int, default=1)
    p.add_argument('--regex'   , type=str, default=None)
    args = p.parse_args()

    for name in sorted(os.listdir('tarballs')):

        image_name = name.removesuffix('.tar.zst')
        if args.regex and not re.match(args.regex, image_name):
            continue

        values = bench_engine(image_name, args.seconds, args.threads, args.seconds * 2)
        avg    = sum(values) / len(values)
        print ('%-40s %8d' % (image_name, avg))
