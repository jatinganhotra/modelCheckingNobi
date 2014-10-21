import sys
import numpy as np
import math
import os

def lognstat(mu, sigma):
  """Calculate the mean and variance of the lognormal distribution given
     the mean (`mu`) and standard deviation (`sigma`) of the associated
     normal distribution."""
  m = np.exp(mu + sigma**2 / 2.0)
  v = np.exp(2 * mu + sigma**2) * (np.exp(sigma**2) - 1)
  return m, v

def main(numnode, st, en, counts):
  load_cmd = "./YCSBRun.sh -l -n %s >/dev/null 2>&1" % numnode
  os.system(load_cmd)

  st, en = max(st, 1), max(en, 1)
  step = float(en - st) / counts
  for i in xrange(counts):
    m = st + i*step #mean
    v = max(1, (m*0.15)**2) #sd is within 15% of mean
    mu = np.log(m**2 / math.sqrt(v + m**2))
    sigma = math.sqrt(np.log(1 + v/m**2))

    print "%s) mu=%s, sigma=%s, mean=%s, sd=%s" % (i, mu, sigma, m, math.sqrt(v))
    sys.stdout.flush()

    netem_cmd = 'ssh sonnbc@node-00.riak.confluence.emulab.net \
      /scratch/Confluence/riak/netem/set_delay_all.sh %s %s %s >/dev/null' % (numnode, mu, sigma)
    run_cmd = "./YCSBRun.sh -t -n %s | grep INFO > ycsb.log && python YCSBResultParser.py ycsb.log" % numnode
    os.system(netem_cmd)
    os.system(run_cmd)

if __name__ == "__main__":
  numnode, st, en, counts = [int(x) for x in sys.argv[1:5]]
  main(numnode, st, en, counts)
