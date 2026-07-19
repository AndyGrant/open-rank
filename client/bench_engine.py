#!/usr/bin/env python3

import argparse
import multiprocessing
import os
import queue
import re
import subprocess
import threading
import time

from exceptions import OpenRankBenchingFailed

class PeakMemorySampler(threading.Thread):

    PROC_ERRORS = (FileNotFoundError, ProcessLookupError, PermissionError)

    def __init__(self, image_name, interval=0.2):
        super().__init__(daemon=True)
        self.image_name = image_name
        self.interval = interval
        self.peak_kb = 0
        self.stop_event = threading.Event()
        self.pids = [] # Container main PIDs, resolved once on start

    def read(self, path):
        try:
            with open(path) as fh:
                return fh.read()
        except self.PROC_ERRORS:
            return ''

    def pss_kb(self, pid):
        for line in self.read('/proc/%d/smaps_rollup' % pid).splitlines():
            if line.startswith('Pss:'): # Not Pss_Anon / Pss_File / Pss_Shmem
                return int(line.split()[1]) # kB
        return 0

    def children(self, pid):
        try:
            tids = os.listdir('/proc/%d/task' % pid)
        except self.PROC_ERRORS:
            return []
        return [int(p) for tid in tids for p in self.read('/proc/%d/task/%s/children' % (pid, tid)).split()]

    def process_tree(self, root):
        seen, stack = set(), [root]
        while stack:
            pid = stack.pop()
            if pid not in seen:
                seen.add(pid)
                stack += self.children(pid)
        return seen

    def container_pids(self):
        docker = lambda *args: subprocess.run(
            ['docker', *args], capture_output=True, text=True, check=False).stdout

        pids = []
        for cid in docker('ps', '-q', '--filter', 'ancestor=%s' % self.image_name).split():
            pid = docker('inspect', '-f', '{{.State.Pid}}', cid).strip()
            if pid and pid != '0':
                pids.append(int(pid))
        return pids

    def sample(self):
        return sum(self.pss_kb(pid) for root in self.pids for pid in self.process_tree(root))

    def run(self):
        # Containers are already up by the time the sampler starts, and their
        # main PIDs do not change for the life of the bench, so resolve once.
        self.pids = self.container_pids()
        while not self.stop_event.is_set():
            self.peak_kb = max(self.peak_kb, self.sample())
            self.stop_event.wait(self.interval)

    def stop(self):
        self.stop_event.set()
        self.join()
        return self.peak_kb

def run_engine(image_name, seconds, outqueue, ready_event):

    # Run the engine as our own uid/gid so that its /proc/<pid>/smaps_rollup is
    # a same-uid read for the memory sampler, no CAP_SYS_PTRACE / sudo required.
    proc = subprocess.Popen(
        ['docker', 'run', '-i', '--rm', '--user', '%d:%d' % (os.getuid(), os.getgid()), image_name],
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

    # Only sample memory during the actual search, not the isready warmup
    sampler = PeakMemorySampler(image_name)
    sampler.start()

    try: # Every process deposits exactly one result into the Queue
        end_time = time.time() + max_time
        results = [outqueue.get(timeout=max(0, end_time - time.time())) for f in range(threads)]
        peak_kb = sampler.stop()
        return [f['nps'] for f in results], [f['time'] for f in results], peak_kb

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
        if sampler.is_alive():
            sampler.stop()
        for process in processes:
            process.terminate()
            process.join()
