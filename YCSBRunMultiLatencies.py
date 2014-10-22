import sys
import numpy as np
import math
import os
from datetime import datetime
def lognstat(mu, sigma):
  """Calculate the mean and variance of the lognormal distribution given
     the mean (`mu`) and standard deviation (`sigma`) of the associated
     normal distribution."""
  m = np.exp(mu + sigma**2 / 2.0)
  v = np.exp(2 * mu + sigma**2) * (np.exp(sigma**2) - 1)
  return m, v

def get_hosts(numnode):
  cmd =" \
    for (( i = 0; i < %s; i++)); do \n \
      ssh sonnbc@node-0$i.riak.confluence.emulab.net -C \
        \"ifconfig | grep 10\.1\.1 | tr ':' ' ' | awk '{print \$3}'\" \n \
    done | tr '\\n' ',' \
    " % numnode
  return os.popen(cmd).read()

def set_network_delay(numnode, delay):
  m = delay #mean
  v = max(1, (m*0.15)**2) #sd is within 15% of mean
  mu = np.log(m**2 / math.sqrt(v + m**2))
  sigma = math.sqrt(np.log(1 + v/m**2))

  netem_cmd = 'ssh sonnbc@node-00.riak.confluence.emulab.net \
    /scratch/Confluence/riak/netem/set_delay_all.sh %s %s %s \
    >/dev/null' % (numnode, mu, sigma)

  os.system(netem_cmd)
  print "mean delay = %s, sd = %s" % (m, math.sqrt(v))

def main(numnode, delay, st, en, counts):
  hosts = get_hosts(numnode)
  print "Hosts = %s" % hosts

  load_cmd = "./YCSBRun.sh -l -h %s >/dev/null 2>&1" % hosts
  os.system(load_cmd)

  set_network_delay(numnode, delay):

  st, en = max(st, 1), max(en, 1)
  step = (en - st) / counts
  ts = datetime.now()
  for i in xrange(counts):
    rate = st + i*step #mean

    print "Iteration #%s:" % i
    run_cmd = "./YCSBRun.sh -t %s -h %s | grep INFO > ycsb.log \
              && python YCSBResultParser.py ycsb.log" % (rate, hosts)
    os.system(run_cmd)

    elapsed = (datetime.now()-ts).total_second()
    ts = datetime.now()
    print "time=%s, rate=%s (ops/s) = %s (s/op) check %s" % (elapsed, rate, 1.0/rate, elapsed/100) #100 is ops count

if __name__ == "__main__":
  numnode, latency,  st, en, counts = [int(x) for x in sys.argv[1:6]]
  main(numnode, delay, st, en, counts)
