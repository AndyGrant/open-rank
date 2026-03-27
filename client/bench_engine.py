#!/usr/bin/env python3

import argparse
import multiprocessing
import queue
import re
import subprocess
import time

def run_engine(image_name, seconds, outqueue):

    proc = subprocess.Popen(
        ['docker', 'run', '-i', '--rm', image_name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    proc.stdin.write('uci\n')
    proc.stdin.write('isready\n')
    proc.stdin.flush()

    while proc.stdout.readline().rstrip() != 'readyok':
        pass

    proc.stdin.write('position startpos\n')
    proc.stdin.write('go movetime %d\n' % (seconds * 1000))
    proc.stdin.flush()

    nps = None
    while 'bestmove' not in (line := proc.stdout.readline()):
        if (m := re.search(r'nps\s+(\d+)', line)):
            nps = int(m.group(1))

    proc.stdin.write('quit\n')
    proc.stdin.flush()
    proc.wait()

    outqueue.put(nps)

def bench_engine(image_name, seconds, threads, max_time):

    outqueue = multiprocessing.Queue()

    processes = [
        multiprocessing.Process(
            target=run_engine,
            args=(image_name, seconds, outqueue)
        ) for f in range(threads)
    ]

    for process in processes:
        process.start()

    try: # Every process deposits exactly one result into the Queue
        end_time = time.time() + max_time
        return [outqueue.get(timeout=max(0, end_time - time.time())) for f in range(threads)]

    except queue.Empty:

        # Find container ids for all of the spawned containers
        container_ids = subprocess.run(
            ['docker', 'ps', '-q', '--filter', 'ancestor=%s' % image_name],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip().split('\n')

        # Kill all docker containers with this image
        for container_id in container_ids:
            print ('Killing container %s for %s' % (container_id, image_name))
            subprocess.run(['docker', 'kill', container_id], capture_output=True, check=False)

        raise Exception('Benchmark exceeded max_time of %d seconds for %s' % (max_time, image_name))

    finally: # Terminate any still-running processes and join to avoid zombies
        for process in processes:
            process.terminate()
            process.join()
