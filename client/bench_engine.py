#!/usr/bin/env python3

import argparse
import multiprocessing
import queue
import re
import subprocess
import time

from exceptions import OpenRankBenchingFailed

def run_engine(image_name, seconds, outqueue, ready_event):

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

    # Block here until main thread sets the ready flag
    ready_event.wait()

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

    outqueue.put({ 'nps' : nps, 'time' : time.time() })

def bench_engine(image_name, threads, seconds, max_time, ready_delay=5):

    outqueue = multiprocessing.Queue()
    ready_event = multiprocessing.Event()

    processes = [
        multiprocessing.Process(
            target=run_engine,
            args=(image_name, seconds, outqueue, ready_event)
        ) for f in range(threads)
    ]

    for process in processes:
        process.start()

    # Give some time to let the engines all finish the isready cycle
    time.sleep(ready_delay)
    ready_event.set()

    try: # Every process deposits exactly one result into the Queue
        end_time = time.time() + max_time
        results = [outqueue.get(timeout=max(0, end_time - time.time())) for f in range(threads)]
        return [f['nps'] for f in results], [f['time'] for f in results]

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

        raise OpenRankBenchingFailed('Benchmark exceeded max_time of %d seconds for %s' % (max_time, image_name))

    finally: # Terminate any still-running processes and join to avoid zombies
        for process in processes:
            process.terminate()
            process.join()
