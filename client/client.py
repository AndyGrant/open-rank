#!/usr/bin/env python3

import argparse
import hashlib
import io
import json
import os
import pathlib
import psutil
import requests
import subprocess
import tarfile
import tempfile
import zstandard as zstd

from exceptions import *
from bench_engine import bench_engine
from hardware import HardwareConfig
from schemas import *

OPENRANK_BENCH_TIME_SECONDS   = 10
OPENRANK_BENCH_TIME_THRESHOLD = 30
OPENRANK_BENCH_TIME_DELAY     = 5

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

def get_fastchess_version(fastchess_path):
    try:
        return subprocess.run(
            [str(fastchess_path), '--version'],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def load_tarball_shas():
    if os.path.exists('tarballs.info'):
        with open('tarballs.info') as fin:
            return json.loads(fin.read())
    return {}


def parse_arguments():

    # We can use ENV variables for the Username, Password, and Server
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
    p.add_argument('-T', '--threads' , help='Default: nthreads - 1')

    # Replace with ENV variables if needed
    args, unknown = p.parse_known_args()
    args.username = args.username if args.username else os.environ['OPENRANK_USERNAME']
    args.password = args.password if args.password else os.environ['OPENRANK_PASSWORD']
    args.server   = args.server   if args.server   else os.environ['OPENRANK_SERVER'  ]
    args.threads  = args.threads  if args.threads  else max(1, psutil.cpu_count(logical=False) - 1)

    return args

def determine_scale_factor(args, auth_data, engine):

    print ('Running benchmark for %s on %d threads' % (engine.image, args.threads))

    try:
        nps_values, endtimes = bench_engine(
            engine.image,
            args.threads,
            OPENRANK_BENCH_TIME_SECONDS,
            OPENRANK_BENCH_TIME_THRESHOLD,
            OPENRANK_BENCH_TIME_DELAY
        )
    except OpenRankBenchingFailed as error:
        raise error

    avg_nps    = sum(nps_values) / len(nps_values)
    factor     = avg_nps / engine.nps
    max_delta  = max(endtimes) - min(endtimes)
    nps_spread = max(nps_values) - min(nps_values)

    print ('... NPS from server is %d' % (engine.nps))
    print ('... NPS from local run is %d' % (avg_nps))
    print ('... Relative factor for this machine is %.2f' % (factor))
    print ('... Max time spread of %.3fs, nps spread of %d\n' % (max_delta, nps_spread))

    return factor


def client_connect(args, hwinfo):

    secret = worker_id = None

    if os.path.exists('worker.info'):
        with open('worker.info', 'r') as f:
            secret, worker_id = f.read().strip().split()
            worker_id = int(worker_id)

    req = ConnectRequest(
        username  = args.username,
        password  = args.password,
        hardware  = vars(hwinfo),
        worker_id = worker_id,
        secret    = secret,
    )

    resp = requests.post(url_join(args.server, 'client/connect/'), json=req.model_dump()).json()

    if 'error' in resp:
        raise OpenRankAuthenticationError(resp['error'])

    connect_resp = ConnectResponse.model_validate(resp)

    with open('worker.info', 'w') as f:
        f.write('%s %s' % (connect_resp.secret, connect_resp.worker_id))

    return {
        'secret'    : connect_resp.secret,
        'worker_id' : connect_resp.worker_id,
    }

def client_request_work(args, auth_data):

    resp = requests.post(url_join(args.server, 'client/request_work/'), json=auth_data).json()

    if 'error' in resp:
        raise OpenRankGeneralRequestError(resp['error'])

    if 'warning' in resp:
        print(resp['warning'])
        return None

    return WorkloadResponse.model_validate(resp)

def client_pull_fastchess(args, auth_data, expected_ver):

    fastchess_path = pathlib.Path(__file__).resolve().parent / 'fastchess'
    print ('Preparing Fastchess executable')

    # Check if fastchess exists and get its version
    current_ver = get_fastchess_version(fastchess_path)
    if current_ver:
        print ('... Found local fastchess version: %s' % (current_ver))

    # If version matches, we're good
    if current_ver == expected_ver:
        print ('... Version matches expected: %s\n' % (expected_ver))
        return

    # Need to download fastchess
    print ('... Downloading expected version: %s' % (expected_ver))

    req = PullFastchessRequest(
        worker_id = auth_data['worker_id'],
        secret    = auth_data['secret'],
    )

    resp = requests.post(url_join(args.server, 'client/pull_fastchess/'), json=req.model_dump(), stream=True)

    if resp.headers.get('Content-Type', '').startswith('application/json'):
        raise OpenRankGeneralRequestError(resp.json()['error'])

    with open(fastchess_path, 'wb') as f:
        for chunk in iter(lambda: resp.raw.read(1024 * 1024), b''):
            f.write(chunk)

    os.chmod(fastchess_path, 0o755)

    # Verify the version
    downloaded_ver = get_fastchess_version(fastchess_path)
    print ('... Downloaded version: %s\n' % (downloaded_ver))

    if downloaded_ver != expected_ver:
        raise OpenRankMismatchedFastchessError()

def client_pull_image(args, auth_data, engine_info, tarball_shas):

    image_name = engine_info.image
    print ('Preparing Docker Image for %s' % (image_name))

    if tarball_shas.get(image_name) == engine_info.sha256 and image_exists(image_name):
        print ('... Found Docker Image for %s locally\n' % (image_name))
        return

    req = PullImageRequest(
        worker_id = auth_data['worker_id'],
        secret    = auth_data['secret'],
        engine_id = engine_info.engine_id,
    )

    resp = requests.post(url_join(args.server, 'client/pull_image/'), json=req.model_dump(), stream=True)

    if resp.headers.get('Content-Type', '').startswith('application/json'):
        raise OpenRankGeneralRequestError(resp.json()['error'])

    with tempfile.NamedTemporaryFile() as zst_tmp:

        # Download the .tar.zst without modifying it
        print ('... Downloading %s.tar.zst' % (image_name))
        for chunk in iter(lambda: resp.raw.read(1024 * 1024), b''):
            zst_tmp.write(chunk)
        zst_tmp.flush()

        # Compare against the expected sha256 from the server
        compressed_sha = sha256_for_file(pathlib.Path(zst_tmp.name))
        print('... Expected SHA256: %s' % (engine_info.sha256))
        print('... Compressed SHA256: %s' % (compressed_sha))
        zst_tmp.seek(0) # Go back to the start of the file for reading

        if engine_info.sha256 != compressed_sha:
            raise OpenRankCorruptedTarballError('Corrupted download for %s' % (image_name))

        with tempfile.NamedTemporaryFile(suffix='.tar') as tmp_tar:

            # Decompress now to a temporary .tar file
            with zstd.ZstdDecompressor().stream_reader(resp.raw) as reader:
                for chunk in iter(lambda: reader.read(1024 * 1024), b''):
                    tmp_tar.write(chunk)
            tmp_tar.flush()

            # Finally, load the file into docker from the .tar
            print ('... Loading Docker Image from %s.tar\n' % (image_name))
            subprocess.run(['docker', 'load', '-i', tmp_tar.name], capture_output=True, text=True)

    if not image_exists(image_name):
        raise OpenRankFailedDockerLoadError('Could not load %s' % (image_name))

    # Save the tarball sha long term to check against on each workload
    tarball_shas[image_name] = engine_info.sha256
    with open('tarballs.info', 'w') as fout:
        fout.write(json.dumps(tarball_shas, indent=4))

def client_pull_book(args, auth_data, book_info):

    book_name = book_info.name
    book_path = pathlib.Path(__file__).resolve().parent / 'books' / book_name
    print ('Looking for Book at %s' % (book_path))

    if os.path.exists(book_path):
        print ('... Found %s locally\n' % (book_name))
        return

    req = PullBookRequest(
        worker_id      = auth_data['worker_id'],
        secret         = auth_data['secret'],
        rating_list_id = book_info.rating_list_id,
    )

    print ('Downloading Book Archive for %s...' % (book_name))
    resp = requests.post(url_join(args.server, 'client/pull_book/'), json=req.model_dump(), stream=True)

    if resp.headers.get('Content-Type', '').startswith('application/json'):
        raise OpenRankGeneralRequestError(resp.json()['error'])

    with tempfile.NamedTemporaryFile() as zst_tmp:

        print('... Downloading %s.zst' % (book_name))
        for chunk in iter(lambda: resp.raw.read(1024 * 1024), b''):
            zst_tmp.write(chunk)
        zst_tmp.flush()

        compressed_sha = sha256_for_file(pathlib.Path(zst_tmp.name))
        print('... Expected SHA256: %s' % (book_info.sha256))
        print('... Compressed SHA256: %s' % (compressed_sha))
        zst_tmp.seek(0) # Go back to the start of the file for reading

        if book_info.sha256 != compressed_sha:
            raise OpenRankCorruptedBookError('Corrupted download for %s' % (book_name))

        with book_path.open('wb') as book_file:
            print('... Decompressing to %s\n' % (book_name))
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

    hwinfo       = HardwareConfig()             # Check if the machine is even allowed
    args         = parse_arguments()            # Username, Password, Server
    auth_data    = client_connect(args, hwinfo) # All requests will contain auth_data
    tarball_shas = load_tarball_shas()          # Record of SHAs for all loaded tarballs

    if not (workload := client_request_work(args, auth_data)):
        print('No work available')
        exit()

    client_pull_fastchess(args, auth_data, workload.fastchess_version)
    client_pull_image(args, auth_data, workload.engine_a, tarball_shas)
    client_pull_image(args, auth_data, workload.engine_b, tarball_shas)
    client_pull_book(args, auth_data, workload.book)

    scale_a = determine_scale_factor(args, auth_data, workload.engine_a)
    scale_b = determine_scale_factor(args, auth_data, workload.engine_b)
    scale   = (scale_a + scale_b) / 2
