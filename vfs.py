#!/bin/env python3
import pyfuse3
import trio
from numpy import (uint64, uint32) 
import errno
from stat import (S_IFREG, S_IFDIR)
import sqlite3

class Directory:
    async def read(self, start_id):
        pass

    async def __getitem__(self, key):
        pass

    async def release(self):
        pass

class File:
    async def read(self, off, size):
        pass

    async def release(self):
        pass

class iNode:
    '''
    contains metadata and opening method
    '''
    def __init__(self, acquire, size = None, mtime = None):
        self.acquire = acquire
        self.size = size
        self.mtime = mtime

class VirtualFS(pyfuse3.Operations):
    class Mapping:
        def __init__(self, index_type, mapping = {}):
            self.index = index_type(0)
            self.mapping = mapping
    
        def allocate(self, x):
            while self.index in self.mapping:
                self.index += 1
            self.mapping[self.index] = x
            return self.index

        def __getitem__(self, i):
            return self.mapping[i]

        def deallocate(self, i):
            return self.mapping.pop(i)

    off_t = uint64
    fh_t = uint64
    inode_t = uint32

    def __init__(self, root):
        super(VirtualFS, self).__init__()
        self.supports_dot_lookup = False
        self.enable_writeback_cache = False

        self.inode = VirtualFS.Mapping(VirtualFS.inode_t, {pyfuse3.ROOT_INODE:root})
        self.fh = VirtualFS.Mapping(VirtualFS.fh_t)

    async def open(self, inode, flags, ctx=None):
        inode_obj = self.inode[inode]
        fh_obj = await inode_obj.acquire()
        fi = pyfuse3.FileInfo()
        fi.fh = self.fh.allocate(fh_obj)
        fi.direct_io = True
        fi.keep_cache = False
        fi.nonseekable = False
        return fi

    async def release(self, fh):
        obj = self.fh.deallocate(fh)
        await obj.release()

    async def read(self, fh, off, size):
        obj = self.fh[fh]
        data = await obj.read(off, size)
        return data

    async def opendir(self, inode, ctx):
        inode_obj = self.inode[inode]
        fh_obj = await inode_obj.acquire()
        return self.fh.allocate(fh_obj)

    async def getattr(self, inode, ctx):
        inode_obj = self.inode[inode]
        return self.__makeattr(inode, inode_obj)
        
    def __makeattr(self, inode, inode_obj):
            attr = pyfuse3.EntryAttributes()
            attr.st_ino = inode
            if inode_obj.size is None:
                    attr.st_mode = S_IFDIR
                    attr.st_size = 0
            else:
                    attr.st_mode = S_IFREG
                    attr.st_size = inode_obj.size
            attr.st_mtime_ns = inode_obj.mtime
            attr.st_mode |= 0o777
            attr.st_uid = 0
            attr.st_gid = 0
            return attr

    async def readdir(self, fh, start_id, token):
        obj = self.fh[fh]

        async for (name, inode_obj, next_id) in obj.read(start_id):
            inode = self.inode.allocate(inode_obj)
            attr = self.__makeattr(inode, inode_obj)
            if not pyfuse3.readdir_reply(token, name, attr, next_id):
                self.inode.deallocate(inode)
                break
    
    async def releasedir(self, fh):
        obj = self.fh.deallocate(fh)
        await obj.release()

    async def forget(self, inode_list):
        for (inode, _) in inode_list:
            self.inode.deallocate(inode)

    async def lookup(self, parent_inode, name, ctx):
        parent_inode_obj = self.inode[parent_inode]
        parent_fh_obj = await parent_inode_obj.acquire()
        inode_obj = await parent_fh_obj[name]
        await parent_fh_obj.release()
        if inode_obj is None:
            raise pyfuse3.FUSEError(errno.ENOENT)
        else:
            inode = self.inode.allocate(inode_obj)
            return self.__makeattr(inode, inode_obj)