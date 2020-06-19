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
    parser.add_argument('--database', '-d', type=str, help='the sqlite3 database file', default='faptrack.db')
    args = parser.parse_args()
    
    my_opts = set(pyfuse3.default_options)
    my_opts.add('allow_root')
    my_opts.discard('default_permissions')

    def conn_fac():
        return sqlite3.connect(args.database)
    pyfuse3.init(VirtualFS(trackFS(conn_fac)), args.mountpoint, my_opts)
    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close()
        raise

    pyfuse3.close()

if __name__ == '__main__':
    main()
