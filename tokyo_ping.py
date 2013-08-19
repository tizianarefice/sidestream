#! /usr/bin/python -u

"""
tokyo-ping.py: Poll for newly closed connections and probe the remote address with different paris-traceroute flow-ids as well as ping. Output is sent to a log file.
"""

print "Starting tokyo-ping"

from Web100 import *
import paris_traceroute
import subprocess
import sys
import time

class TokyoPing():
    n_probes = 10
    inter_probe_gap_ms = 200
    n_flow_ids = 32
    separator = '=== %s id=%d ==='


olddir=""
logc = 0
def getlogf(t):
    global logf, server, logc
    logdir = time.strftime("%Y/%m/%d/", time.gmtime(t))
    if olddir and olddir!=logdir:
        paris_traceroute.postproc(olddir)
    paris_traceroute.mkdirs(logdir+paris_traceroute.server)
    logname = time.strftime("%Y/%m/%d/%%s%Y%m%dT%TZ_ALL%%d.tokyo",
                            time.gmtime(t)) % (server, logc)
    logc+=1
    return open(logname, "a")

def do_ping(rem_address):
    # Ignore connections to loopback and Planet Lab Control (PLC)
    if rem_address == "127.0.0.1":
        return
    if rem_address.startswith("128.112.139"):
        return

    # pick/open a logfile as needed, based on the close poll time
    t = time.time()
    logf = getlogf(t)

    logf.write(TokyoPing.separator % ('ping', 0))
    process = subprocess.Popen(["ping",
        "-i 0.%d" % TokyoPing.inter_probe_gap_ms,
        "-c %d" % TokyoPing.n_probes,
        rem_address], stdout = subprocess.PIPE)
    (so,se) = process.communicate()
    logf.write(so)
    logf.write("\n")

    for i in xrange(1, TokyoPing.n_flow_ids):
        logf.write(TokyoPing.separator % ('paris', i))
        process = subprocess.Popen(
            ["paris-traceroute",
             "-p icmp", "-f 60", "-m 60", "-L 56",
             "-w %d" % TokyoPing.inter_probe_gap_ms,
             "-n", "-q %d" % TokyoPing.n_probes, "-d %d" % i,
             rem_address], stdout = subprocess.PIPE)
        (so,se) = process.communicate()
        logf.write(so)
        logf.write("\n")
    logf.close()


server=""
def main():
    # Main
    global server
    if len(sys.argv) == 1:
        server = ""
    elif len(sys.argv) == 2:
        server = sys.argv[1]+"/"
    else:
        print "Usage: %s [server_name]" % sys.argv[0]
        sys.exit()

    recent_ips = paris_traceroute.RecentList()

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
                        if (paris_traceroute.is_valid_ipv4_address(rem_ip) and
                           not recent_ips.contain(rem_ip)):
                            print "Running trace to: %s" % rem_ip
                            do_ping(rem_ip)
                            recent_ips.add(rem_ip)
            except Exception, e:
                print "Exception:", e
                pass
        closed = newclosed
        time.sleep(5)


if __name__ == "__main__":
    main()
