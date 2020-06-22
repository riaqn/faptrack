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

    parser_add = subparsers.add_parser('add', help='add videos')
    parser_add.add_argument('file', type=str, nargs='+',help='videos to add to the database')
    parser_add.add_argument('-r', '--recursive', action='store_true', help='scan folder recursively')
    
    parser_list = subparsers.add_parser('list', help='list videos')
    parser_list.add_argument('-o', '--offset', type=int, help='offset', default=0)
    parser_list.add_argument('-l', '--limit', type=int, help='limit', default=100)

    parser_reset = subparsers.add_parser('reset', help='reset history of a video')
    parser_reset.add_argument('vid', type=str, nargs='+', help='videos to reset')

    args = parser.parse_args()

    conn = sqlite3.connect(args.database)
    conn.isolation_level = 'DEFERRED'

    if args.subcmd == 'add':
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
                logging.error('No videos are added in %s', path)
                break

        if flag:
            conn.commit()
        else:
            conn.rollback()
        
    elif args.subcmd == 'list':
        for row in conn.execute('SELECT vid, avg_avg_view_time, path from videos where view_count > 0 ORDER BY avg_avg_view_time DESC LIMIT ? OFFSET ?', (args.limit, args.offset)):
            print(row[0],row[1], row[2])
    elif args.subcmd == 'reset':
        c = conn.cursor()
        for vid in args.vid:
            c.execute('update videos set view_count=0,view_time=0 where vid=?', (vid, ))
        conn.commit()
    else:
        logging.error('No subcmd provided')
    conn.close()
if __name__ == "__main__":
    main()