#! /usr/bin/python -u

"""
tokyo_ping.py: Poll for newly closed connections and probe the remote address with different paris-traceroute flow-ids as well as ping. Output is sent to a log file.


Expected output should look like:

=== ping id=0 ===
PING 74.125.24.99 (74.125.24.99) 56(84) bytes of data.
64 bytes from 74.125.24.99: icmp_seq=1 ttl=51 time=15.7 ms
64 bytes from 74.125.24.99: icmp_seq=2 ttl=51 time=18.9 ms
64 bytes from 74.125.24.99: icmp_seq=3 ttl=51 time=19.2 ms
64 bytes from 74.125.24.99: icmp_seq=4 ttl=51 time=13.0 ms
64 bytes from 74.125.24.99: icmp_seq=5 ttl=51 time=12.3 ms
64 bytes from 74.125.24.99: icmp_seq=6 ttl=51 time=13.2 ms
64 bytes from 74.125.24.99: icmp_seq=7 ttl=51 time=22.0 ms
64 bytes from 74.125.24.99: icmp_seq=8 ttl=51 time=15.7 ms
64 bytes from 74.125.24.99: icmp_seq=9 ttl=51 time=24.6 ms
64 bytes from 74.125.24.99: icmp_seq=10 ttl=51 time=26.2 ms

--- 74.125.24.99 ping statistics ---
10 packets transmitted, 10 received, 0% packet loss, time 1804ms
rtt min/avg/max/mdev = 12.365/18.138/26.233/4.687 ms
=== paris id=1 ===
traceroute [(192.168.0.12:33456) -> (74.125.24.99:1)], protocol icmp, algo hopbyhop, duration 2 s
60  74.125.24.99  39.644 ms   29.497 ms   31.519 ms   31.144 ms   18.418 ms   81.543 ms   57.557 ms   33.388 ms   25.026 ms   56.255 ms
=== paris id=2 ===
[...]
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
    s.serve(function=do_ping, node=server)


if __name__ == "__main__":
    main()
