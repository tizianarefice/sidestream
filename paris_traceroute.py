#! /usr/bin/python -u

"""
paris_traceroute.py: Poll for newly closed connections and print a traceroute to
the remote address to a log file.
"""

print "Starting paris-traceroute"

from utils import IPAddressUtils
from utils import LogFileUtils
from utils import GeneralServingLoop
import subprocess
import sys
import time

class ParisTraceroute:
    label = 'paris-traceroute'


def do_traceroute(rem_address, node):
    if not IPAddressUtils.is_remote_address(rem_address):
        return
    # pick/open a logfile as needed, based on the close poll time
    t = time.time()
    logf = LogFileUtils.getlogf(t, ParisTraceroute.label, node)
    process = subprocess.Popen(["paris-traceroute","-picmp","--algo=exhaustive",rem_address],
                               stdout = subprocess.PIPE)
    (so,se) = process.communicate()
    logf.write(so)
    logf.write("\n")
    logf.close()


def main():
    # Main
    server=""
    if len(sys.argv) == 1:
        server=""
    elif len(sys.argv) == 2:
        server=sys.argv[1]+"/"
    else:
        print "Usage: %s [server_name]" % sys.argv[0]
        sys.exit()
    s = GeneralServingLoop(ParisTraceroute.label)
    s.serve(function=do_traceroute, node=server)


if __name__ == "__main__":
    main()
