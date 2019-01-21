#!/usr/bin/env python3
import subprocess
import sys
import argparse
import itertools
import os
import time
import threading
import datetime

default_opts_pfx = ['ffmpeg', '-hide_banner']
default_opts_proc = [ '-c:v', 'libx264', '-preset', 'veryfast', '-f', 'mp4']
opt_heading = ['x264-params']

# This dictionary represents the set of parameters we want to sweep over specified as
# parameter name and an iterable over the values we would like.
params_to_try = {\
        # Max keyframe
        'keyint': range(125, 550, 250),
        'min-keyint': range(2, 50, 10),
        'b-adapt': [2],
        'bframes': range(0, 10, 5),
        'deframe': range(-3,3, 2),
        'crf': range(18, 26, 3),
        'chroma-qp-offset': range(-10, 2, 3),
        'aq-mode': range(0, 4, 2),
        'partitions': ['none', 'all'],
        'direct': ['spatial', 'temporal', 'auto'],
        'direct-8x8': range(-1, 2, 2),
        'me': ['dia', 'hex', 'umh', 'esa', 'tesa'],
        'merange': range(4, 17, 3),
        'subme': range(0, 10, 5)
}

# This represents (in order) the set of parameters for which we want to prioritize exploration. Later parameters
# have higher priority.
prioritize = []
# This represents (in order) the set of fields for which we want to depriroitize exploration. Earlier parameters have
# lower priority
deprioritize = ['subme', 'partitions', 'min-keyint']

def gen_opts():
    all_keys = list(params_to_try.keys())
    keys_to_sort = list(set(all_keys) - set(prioritize) - set(deprioritize))
    keys = deprioritize + sorted(keys_to_sort) + prioritize
    vals = [params_to_try[k] for k in keys]
    for opts in itertools.product(*vals):
        assert(len(opts) == len(all_keys))
        s = ':'.join(map(lambda t: t[0]+'='+str(t[1]), zip(keys, opts)))
        yield s

def run_ffmpeg_opts(name, opts, i, duration, output):
    # FIXME: Generalize this bit
    opts = default_opts_pfx + ['-i', i, '-ss', '00:00:00', '-to', duration] + default_opts_proc  + opts + [output] # output must always be the last arg
    p = subprocess.run(opts, capture_output=True, check=True)
    return (p.stderr, p.stdout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', help='How much of the video to process (seconds)', type=int, default=60)
    parser.add_argument('input', help='Video to use as input')
    parser.add_argument('prefix', help='Prefix for output')
    args = parser.parse_args()
    duration_string = str(datetime.timedelta(seconds=args.duration))
    print("Triming to %s"%duration_string, file=sys.stderr)
    print("Arguments Size Time")
    out_file = args.prefix + '_out.mp4'
    for o in gen_opts():
        try:
            start = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) 
            (err, out) = run_ffmpeg_opts(args.prefix, ['-x264-params', o], args.input, duration_string, out_file)
            end = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
            sz = os.path.getsize(out_file)
            print(o, sz, end-start)
            os.remove(out_file)
            # normalize = o.replace(':', '$')
            # with open(normalize + '.err', 'wb') as efile:
                # efile.write(err)
            # with open(normalize + '.out', 'wb') as ofile:
                # ofile.write(out)
        except subprocess.CalledProcessError:
            print(o, "-err-")
