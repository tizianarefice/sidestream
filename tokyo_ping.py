#! /usr/bin/python -u

"""
tokyo-ping.py: Poll for newly closed connections and probe the remote address with different paris-traceroute flow-ids as well as ping. Output is sent to a log file.
"""

print "Starting tokyo-ping"

from utils import IPAddressUtils
from utils import LogFileUtils
from utils import GeneralServingLoop
import subprocess
import sys
import time

class TokyoPing():
    n_probes = 10
    inter_probe_gap_ms = 200
    n_flow_ids = 32
    separator = '=== %s id=%d ==='
    label = 'tokyo-ping'


def do_ping(rem_address, node):
    if not IPAddressUtils.is_remote_address(rem_address):
        return
    # pick/open a logfile as needed, based on the close poll time
    t = time.time()
    logf = LogFileUtils.getlogf(t, TokyoPing.label, node)

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


def main():
    # Main
    server=""
    if len(sys.argv) == 1:
        server = ""
    elif len(sys.argv) == 2:
        server = sys.argv[1]+"/"
    else:
        print "Usage: %s [server_name]" % sys.argv[0]
        sys.exit()
    s = GeneralServingLoop(TokyoPing.label)
    s.serve(do_ping, server)


if __name__ == "__main__":
    main()
