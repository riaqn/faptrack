from vfs import (iNode, Directory, File)
import sqlite3
import os
import time

'''
Track albums or videos?
1. We do want to know which video is the best in an album
2. but the quality of videos in an albums are correlated; we want to use that information. But I guess you can just view the videos anyway - no need to be lazy


database: contains two tables:
1. albums. aid, view_time, view_count
2. videos. vid, aid, path
'''

def gettime():
        return time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        
class TrackedFile(File):
    def __init__(self, vid, path, conn):
        self.vid = vid
        self.conn = conn
        self.fd = open(path, 'rb')
        print(vid, path, "opened")
        self.time = gettime()

    async def read(self, off, size):
        print(gettime()/(10**9), self.vid, size)
        self.fd.seek(off)
        return self.fd.read(size)

    async def release(self):
        cur = gettime()
        view_time = cur - self.time
        print(self.vid, "closed", view_time)
        self.conn.execute('UPDATE videos SET view_time = view_time + ?, view_count = view_count + 1 WHERE vid = ?', (view_time, self.vid))
        self.conn.commit()

        self.fd.close()

class TrackedDirectory(Directory):
    def __init__(self, conn_fac):
        self.conn_fac = conn_fac
        self.conn = conn_fac()
        self.conn.isolation_level = "DEFERRED"

    def __make_inode(self, vid, path, mtime):
        async def op():
            return TrackedFile(vid, path, self.conn_fac())
        size = os.path.getsize(path)
        inode = iNode(op, size, mtime)
        return inode

    async def read(self, start_id):
        c = self.conn.cursor()
        i = start_id
        for (vid, path) in c.execute("SELECT vid, path FROM videos_avg_avg_view_time LIMIT -1 OFFSET ?", (start_id,)):
            if i >= 100:
                break
            name = os.path.basename(path)
            mtime = i * (10**9)
            inode = self.__make_inode(vid, path, mtime)
            i += 1
            yield (name.encode(), inode, i)

    async def release(self):
        self.conn.close()

def trackFS(conn_fac):
    async def __op():
        return TrackedDirectory(conn_fac)
    return iNode(__op, None, gettime())