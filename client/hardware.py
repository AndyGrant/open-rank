#!/usr/bin/env python3

import cpuinfo
import platform
import psutil
import re
import subprocess
import uuid

from exceptions import *

class HardwareConfig:

    def __init__(self):

        # CPU Info
        info = cpuinfo.get_cpu_info()
        self.cpu_flags = list(map(str.lower, info.get('flags', [])))
        self.cpu_name  = info.get('brand_raw', info.get('brand', 'Unknown'))
        self.arch      = self.get_arch(info)

        # OS Info
        self.os_name    = platform.system()
        self.os_ver     = platform.release()
        self.python_ver = platform.python_version()

        # Hardware Info
        self.mac_address    = hex(uuid.getnode()).lower()[2:]
        self.logical_cores  = psutil.cpu_count(logical=True)
        self.physical_cores = psutil.cpu_count(logical=False)
        self.ram_total_mb   = psutil.virtual_memory().total // (1024 ** 2)

        # NUMA Info
        self.numa_nodes, self.numa_maps = self.get_numa_core_mapping()

        # Track znver1/znver2 which have failing PEXT support
        self.cxx_compiler, is_znver1, is_znver2 = self.detect_old_zen_versions()

        self.validate_hardware(is_znver1, is_znver2)

    def get_arch(self, info):
        if info.get('arch', '').lower() in ('x86_64', 'amd64', 'x86'):
            return 'x86'
        elif info.get('arch', '').lower() in ('arm', 'arm64', 'aarch64'):
            return 'ARM'
        else: # We don't care, since we are going to require x86 anyway
            return 'UNKNOWN'

    def get_numa_core_mapping(self):
        try:
            numa_text = subprocess.check_output(['numactl', '--hardware'], text=True)
            numa_map = {
                int(n): list(map(int, c.split()))
                for n, c in re.findall(r'node (\d+) cpus: ([\d ]+)', numa_text)
            }
            return len(numa_map), numa_map
        except Exception as error:
            return None, None

    def detect_old_zen_versions(self):
        for cxx in ['g++', 'clang++']:
            try:
                cmd    = [cxx, '-march=native', '-dM', '-E', '-']
                proc   = subprocess.run(cmd, input=b'', stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                macros = proc.stdout.decode('ascii', errors='ignore')
                return cxx, '__znver1' in macros, '__znver2' in macros
            except: pass
        return None, None, None

    def validate_hardware(self, is_znver1, is_znver2):

        if self.arch != 'x86':
            raise OpenRankHardwareReqError('open-rank is only supported for x86 machines')

        if self.os_name != 'Linux':
            raise OpenRankHardwareReqError('open-rank is only supported for Linux machines')

        if 'avx2' not in self.cpu_flags or 'fma' not in self.cpu_flags:
            raise OpenRankHardwareReqError('open-rank is only supported for AVX2 machines with FMA')

        if not self.numa_nodes:
            raise OpenRankHardwareReqError('open-rank failed to determine NUMA information via numactl')

        if is_znver1 is None or is_znver2 is None:
            raise OpenRankHardwareReqError('open-rank failed to determine znver1/znver2 via g++/clang++')

        if is_znver1 or is_znver2:
            raise OpenRankHardwareReqError('open-rank does not support znver1/znver2, due to failing PEXT support')

        if self.logical_cores != 2 * self.physical_cores:
            raise OpenRankHardwareReqError('open-rank suspects this is a P+E system, where threads != cores')

if __name__ == '__main__':
    for key, value in vars(HardwareConfig()).items():
        print (key, value)
