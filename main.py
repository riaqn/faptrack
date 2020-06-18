#!/usr/bin/env python3
import pyfuse3
from vfs import VirtualFS
from trackfs import trackFS
import trio

import argparse

import sqlite3

def main():
    parser = argparse.ArgumentParser(description='Mount a FapTrack filesystem')
    parser.add_argument('mountpoint', type=str, help='the mountpoint')
    args = parser.parse_args()
    
    my_opts = set(pyfuse3.default_options)
    my_opts.add('allow_root')
    my_opts.discard('default_permissions')
    pyfuse3.init(VirtualFS(trackFS), args.mountpoint, my_opts)
    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close()
        raise

    pyfuse3.close()

if __name__ == '__main__':
    main()
