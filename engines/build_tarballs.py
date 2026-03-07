#!/usr/bin/env python3

import argparse
import os
import re
import subprocess

from concurrent.futures import ThreadPoolExecutor, as_completed

DOCKER_DIR    = './dockers'
TARBALL_DIR   = './tarballs'
LOG_FILE_PATH = os.path.join('docker_build.log')

def image_exists(name):
    return subprocess.run(
        ['docker', 'image', 'inspect', name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0

def get_dockerfiles(regex_pattern):
    return [
        filename for filename in sorted(os.listdir(DOCKER_DIR))
        if not regex_pattern or re.match(regex_pattern, filename.rsplit('.Dockerfile', 1)[0])
    ]

def build_image(filename, rebuild, dry_run):

    dockerfile_path = os.path.join(DOCKER_DIR, filename)
    base_name       = filename.rsplit('.Dockerfile', 1)[0]
    image_name      = 'openrank-%s' % (base_name.lower())

    if not rebuild and image_exists(image_name):
        return (filename, True, 'Found image %s for %s' % (image_name, dockerfile_path))

    message = 'Building image %s from %s...' % (image_name, dockerfile_path)

    if dry_run:
        return (filename, True, message + ' (dry run)')

    try:
        build_cmd = ['docker', 'build', '-t', image_name, '-f', dockerfile_path, DOCKER_DIR]
        subprocess.run(build_cmd, check=True, capture_output=True, text=True)

        tar_path = os.path.join(TARBALL_DIR, f'{image_name}.tar')
        save_cmd = ['docker', 'save', '-o', tar_path, image_name]
        subprocess.run(save_cmd, check=True, capture_output=True, text=True)

        compressed_path = tar_path + '.zst'
        compress_cmd = ['zstd', '-f', tar_path, '-o', compressed_path]
        subprocess.run(compress_cmd, check=True, capture_output=True, text=True)

        os.remove(tar_path)
        return (filename, True, message)

    except subprocess.CalledProcessError as e:
        with open(LOG_FILE_PATH, 'a') as f:
            f.write(f'Error building {filename}:\n')
            f.write(e.stdout or '')
            f.write('\n')
            f.write(e.stderr or '')
            f.write('\n' + '=' * 60 + '\n')
        error_msg = 'Failed building %s. Check %s for details.' % (filename, LOG_FILE_PATH)
        return (filename, False, error_msg)

def main():

    p = argparse.ArgumentParser()
    p.add_argument('--dry',     action='store_true', help='Do not actually do anything')
    p.add_argument('--rebuild', action='store_true', help='Rebuild existing images')
    p.add_argument('--regex',   default=None,        help='Regex to match for each .Dockerfile')
    p.add_argument('-j',        action='store_true', help='Use all threads to build concurrently')

    args = p.parse_args()
    max_workers = max(1, os.cpu_count() - 1) if args.j else 1

    os.makedirs(TARBALL_DIR, exist_ok=True)

    with open(LOG_FILE_PATH, 'w') as f:
        f.write('Docker build log begin...\n\n')

    dockerfiles = get_dockerfiles(args.regex)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(build_image, filename, args.rebuild, args.dry): filename
            for filename in dockerfiles
        }

        for future in as_completed(futures):
            filename, success, message = future.result()
            print(message)

if __name__ == '__main__':
    main()
