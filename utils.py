#! /usr/bin/python -u

"""
utils.py: A set of common utilities for sidestream (mostly paris-traceroute and
tokyo-ping. """

from Web100 import *
import errno
import os
import socket
import subprocess
import time
import glob


class LogFileUtils:
    # this dict maps a log label to the last dir where a log was written
    last_dir = {}
    # this dict maps a log label to the next log number to write
    next_id = {}

    @classmethod
    def mkdirs(cls, name):
        """ Fake mkdir -p """
        try:
            os.makedirs(name)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(name): pass
            else: raise

    @classmethod
    def postproc(cls, dir):
        """ Remove all write permissions, compute md5sums, etc """
        for f in glob.glob(dir+"*"):
            os.chmod(f, 0444)
        subprocess.call(
                "find . -type f | xargs md5sum > ../manifest.tmp",
                shell=True, chdir=dir)
        os.rename(dir+"/../manifest.tmp", dir+"/manifest.md5")
        os.chmod(dir+"/manifest.md5", 0555)
        os.chmod(dir, 0555)    # And make it immutable

    @classmethod
    def getlogf(cls, t, label, server):
        cls.next_id.setdefault(label, 0)
        logdir = time.strftime("%Y/%m/%d/", time.gmtime(t))
        if cls.last_dir[label] and cls.last_dir[label] != logdir:
            cls.postproc(cls.last_dir[label])
        cls.mkdirs(logdir + server)
        logname = time.strftime(
                "%Y/%m/%d/%%s%Y%m%dT%TZ_ALL%%d.%%s",
                time.gmtime(t)) % (server, cls.next_id[label], label)
        cls.next_id[label] += 1
        return open(logname, "a")


class IPAddressUtils:
    @classmethod
    def is_remote_address(cls, address):
        # Ignore connections to loopback and Planet Lab Control (PLC)
        if address == "127.0.0.1":
            return False
        if address.startswith("128.112.139"):
            return False
        return True

    @classmethod
    def is_valid_ipv4_address(cls, address):
        try:
            socket.inet_pton(socket.AF_INET, address)
        except AttributeError:
            try:
                socket.inet_aton(address)
            except socket.error:
                return False
        except socket.error:
            return False
        return True

    @classmethod
    def is_valid_ipv6_address(cls, address):
        try:
            socket.inet_pton(socket.AF_INET6, address)
        except AttributeError:
            # This is the case if socket doesn't support IPv6, so it's not strictly
            # accurate to return False, but it is conservative.
            return False
        except socket.error:
            return False
        return True


class RecentList:
    def __init__(self):
        self.iplist = []
        # how long an IP address is considered "recent" for
        self.CACHE_WINDOW = 60 * 10  

    def ip_is_recent(self, arg):
        (ip,ts) = arg
        current_ts = time.time()
        return (current_ts <= ts + self.CACHE_WINDOW)

    def clean(self):
        self.iplist = filter(self.ip_is_recent, self.iplist)

    def add(self, remote_ip):
        self.clean()
        self.iplist.append((remote_ip, time.time()))

    def contain(self, remote_ip):
        self.clean()
        for ip, ts in self.iplist:
            if remote_ip == ip: return True
        return False


class GeneralServingLoop:
    def __init__(self, label):
        self.label = label

    def serve(self, do_serve, server):
        recent_ips = RecentList()
        while True:
            a = Web100Agent()
            closed=[]
            cl = a.all_connections()
            newclosed=[]
            for c in cl:
                try:
                    if c.read('State') == 1:
                        newclosed.append(c.cid)
                        if not c.cid in closed:
                            rem_ip = c.read("RemAddress")
                            if (IPAddressUtils.is_valid_ipv4_address(rem_ip) and 
                                    not recent_ips.contain(rem_ip)):
                                print "Running %s to: %s" % (self.label, rem_ip)
                                do_serve(rem_ip, server)
                                recent_ips.add(rem_ip)
                            #else:
                            #    print "Skipping: %s" % rem_ip
                except Exception, e:
                    print "Exception:", e
            closed = newclosed
            time.sleep(5)
