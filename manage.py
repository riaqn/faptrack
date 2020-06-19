#!/usr/bin/env python3
import sqlite3
import logging

import os
import stat

from pymediainfo import MediaInfo
import argparse

def walk(path):
    yield path
    sta = os.stat(path)
    if stat.S_ISDIR(sta.st_mode):
        for e in os.scandir(path):
            yield from walk(e.path)
    
def main():
    parser = argparse.ArgumentParser(description='Managing video database')
    parser.add_argument('--database', '-d', type=str, help='the sqlite3 database file', default='faptrack.db')
 
    subparsers = parser.add_subparsers(dest='subcmd')

    parser_add = subparsers.add_parser('add', help='adding files')
    parser_add.add_argument('file', type=str, nargs='+',help='files to add to the database')
    parser_add.add_argument('-r', '--recursive', action='store_true')

    args = parser.parse_args()

    if args.subcmd == 'add':
        conn = sqlite3.connect(args.database)
        conn.isolation_level = 'DEFERRED'
        def func(path):
            try:
                media_info = MediaInfo.parse(path)
            except:
                return False
            for track in media_info.tracks:
                if track.track_type == 'Video':
                    conn.execute('INSERT INTO videos (path) VALUES (?)', (path,))
                    return True
            return False

        for path in args.file:
            flag = False
            if args.recursive:
                for p in walk(path):
                    if func(p):
                        print(p)
                        flag = True
            else:
                flag = func(path)
            if not flag:
                log.error('No videos are added in %s', path)
                break

        if flag:
            conn.commit()
        else:
            conn.rollback()
        conn.close()

if __name__ == "__main__":
    main()