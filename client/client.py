#!/usr/bin/env python3

import argparse
import hashlib
import io
import json
import os
import pathlib
import requests
import subprocess
import tarfile
import tempfile
import zstandard as zstd

from exceptions import *
from hardware import HardwareConfig

def url_join(*parts):
    return '/'.join(p.strip('/') for p in parts if p) + '/'

def image_exists(image_name):
    return subprocess.run(
        ['docker', 'image', 'inspect', image_name],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0

def sha256_for_file(file_path):
    sha256 = hashlib.sha256()
    with file_path.open('rb') as fin:
        for chunk in iter(lambda: fin.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def parse_arguments():

    # We can use ENV variables for the Username, Passwords, and Servers
    req_user   = 'OPENRANK_USERNAME' not in os.environ
    req_pass   = 'OPENRANK_PASSWORD' not in os.environ
    req_server = 'OPENRANK_SERVER'   not in os.environ

    help_user   = 'Username. May also be provided via OPENRANK_USERNAME environment variable'
    help_pass   = 'Password. May also be provided via OPENRANK_PASSWORD environment variable'
    help_server = 'Server URL. May also be provided via OPENRANK_SERVER environment variable'

    # Pretty formatting
    p = argparse.ArgumentParser(
        formatter_class=lambda prog:
            argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=10)
    )

    # Create and parse all arguments into a raw format
    p.add_argument('-U', '--username', help=help_user  , required=req_user  )
    p.add_argument('-P', '--password', help=help_pass  , required=req_pass  )
    p.add_argument('-S', '--server'  , help=help_server, required=req_server)

    # Replace with ENV variables if needed
    args, unknown = p.parse_known_args()
    args.username = args.username if args.username else os.environ['OPENRANK_USERNAME']
    args.password = args.password if args.password else os.environ['OPENRANK_PASSWORD']
    args.server   = args.server   if args.server   else os.environ['OPENRANK_SERVER'  ]

    return args

def client_connect(args, hwinfo):

    secret = worker_id = None

    if os.path.exists('worker.info'):
        with open('worker.info', 'r') as f:
            secret, worker_id = f.read().strip().split()

    payload = {
        'username' : args.username,
        'password' : args.password,
        'hardware' : json.dumps(vars(hwinfo)),
    }

    if secret and worker_id:
        payload.update({ 'secret': secret, 'worker_id': worker_id })

    if 'error' in (resp := requests.post(url_join(args.server, 'client/connect/'), data=payload).json()):
        raise OpenRankAuthenticationError(resp['error'])

    with open('worker.info', 'w') as f:
        f.write('%s %s' % (resp['secret'], resp['worker_id']))

    return resp

def client_request_work(args, auth_data):

    if 'error' in (resp := requests.post(url_join(args.server, 'client/request_work/'), data=auth_data).json()):
        raise OpenRankGeneralReqError(resp['error'])

    return resp

def client_pull_image(args, auth_data, engine_json):

    image_name = engine_json['image']

    if image_exists(image_name):
        print ('Found Docker Image for %s locally' % (image_name))
        return

    payload = {
        **auth_data,
        'engine_id' : engine_json['engine_id']
    }

    print ('Downloading Docker Image for %s...' % (image_name))
    resp = requests.post(url_join(args.server, 'client/pull_image/'), data=payload, stream=True)

    if resp.headers.get('Content-Type', '').startswith('application/json'):
        raise OpenRankGeneralReqError(resp.json()['error'])

    with tempfile.NamedTemporaryFile(suffix='.tar') as tmp_tar:

        print ('... Decompressing %s.tar.zst' % (image_name))
        with zstd.ZstdDecompressor().stream_reader(resp.raw) as reader:
            for chunk in iter(lambda: reader.read(1024 * 1024), b''):
                tmp_tar.write(chunk)
        tmp_tar.flush()

        print ('... Loading Docker Image from %s.tar' % (image_name))
        subprocess.run(['docker', 'load', '-i', tmp_tar.name], capture_output=True, text=True)

    if not image_exists(image_name):
        raise OpenRankFailedDockerLoadError('Could not load %s' % (image_name))

    print ('... Docker Image for %s is ready\n' % (image_name))

def client_pull_book(args, auth_data, book_json):

    book_name = book_json['name']
    book_path = pathlib.Path(__file__).resolve().parent / 'books' / book_name

    if os.path.exists(book_path):
        print ('Found %s locally' % (book_name))
        return

    payload = {
        **auth_data,
        'rating_list_id' : book_json['rating_list_id']
    }

    print ('Downloading Book Archive for %s...' % (book_name))
    resp = requests.post(url_join(args.server, 'client/pull_book/'), data=payload, stream=True)

    if resp.headers.get('Content-Type', '').startswith('application/json'):
        raise OpenRankGeneralReqError(resp.json()['error'])

    with tempfile.NamedTemporaryFile() as zst_tmp:

        print('... Downloading %s.zst' % (book_name))
        for chunk in iter(lambda: resp.raw.read(1024 * 1024), b''):
            zst_tmp.write(chunk)
        zst_tmp.flush()

        compressed_sha = sha256_for_file(pathlib.Path(zst_tmp.name))
        print('... Expected SHA256: %s' % (book_json['sha256']))
        print('... Compressed SHA256: %s' % (compressed_sha))

        if book_json['sha256'] != compressed_sha:
            raise OpenRankCorruptedBookError('Corrupted download for %s' % (book_name))

        zst_tmp.seek(0) # Go back to the start of the file for reading
        with book_path.open('wb') as book_file:
            print('... Decompressing to %s' % (book_name))
            with zstd.ZstdDecompressor().stream_reader(zst_tmp) as reader:
                for chunk in iter(lambda: reader.read(1024 * 1024), b''):
                    book_file.write(chunk)
            book_file.flush()

if __name__ == '__main__':

    # Use client.py's path as the base pathway always
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Ensure book/ directory exists to save to
    if not os.path.exists('books'):
        os.makedirs('books')

    # Grab the hardware info first, in case this machine is not allowed
    hwinfo = HardwareConfig()

    # Username, Password, Server
    args = parse_arguments()

    # Going forward, all requests contain secret and worker_id
    auth_data = client_connect(args, hwinfo)

    # Could be { 'warning' : ... }
    workload = client_request_work(args, auth_data)

    print (workload)

    client_pull_image(args, auth_data, workload['engine_a'])
    client_pull_image(args, auth_data, workload['engine_b'])
    client_pull_book (args, auth_data, workload['book'    ])
