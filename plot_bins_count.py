import matplotlib.pyplot as plt
plt.rcParams['backend'] = "template"
import sys
import re
import numpy as np
from collections import namedtuple
import hashlib

def drop_outliers(data):
    mean_duration  = np.mean(data)
    std_dev_one_test = np.std(data)
    filtered = [ e for e in data if (abs(e - mean_duration) <= std_dev_one_test)]
    return filtered

def getbins(latency, count_bins):
    total = len(latency)
    bins = []
    fraction = total/count_bins

    tmp = 0
    while( tmp < count_bins):
        bins.append( latency[ fraction*tmp ] )
        tmp = tmp + 1

    # print bins
    return bins

def getallreads(filename):
  content = []
  with open(filename) as f:
    content = f.readlines()

  return content

def getreadsforbin(all_reads, b, prev_bin):
    count = 0
    for r in all_reads:
        if ( int(r) <= b and int(r)  >= prev_bin):
            count = count + 1

    return count

def getreadsperBin(all_reads, bins):
    read_per_bin = {}
    prev_bin = 0
    for b in bins:
        reads_in_bin = getreadsforbin(all_reads, b, prev_bin)
        prev_bin = b
        read_per_bin[b] = reads_in_bin

    return read_per_bin

def main():
    filename = sys.argv[1]
    filename_all_reads = sys.argv[2]
    with open(filename) as f:
        content = f.readlines()

    # Note that the latency values are already sorted
    latency = []
    for l in content:
        latency.append(int(l))

    # Remove the outliers
    #latency = drop_outliers(latency)

    # Find bins
    count_bins =  20
    bins = getbins(latency, count_bins)

    all_reads = getallreads(filename_all_reads)
    #print "Size of all reads is = " + str(int(len(all_reads)))
    # Find good probability in each bin
    reads_per_bin = getreadsperBin(all_reads, bins)
    #print reads_per_bin

    good_reads_per_bin = getreadsperBin(latency, bins)
    #print good_reads_per_bin

    # Get percentage of good per bin
    result = {}
    prev_key = 0;
    for k in good_reads_per_bin.keys():
        if (reads_per_bin[k] == 0):
            if (prev_key != 0):
                result[k] = result[prev_key]
            continue
        result[k] = good_reads_per_bin[k] / float(reads_per_bin[k])
        if (result[k] <= 0.2 and prev_key != 0):
            result[k] = result[prev_key]
        prev_key = k

    #print "--------------------------"
    #print result

    f = open("result.txt", "w+")
    for k in result.keys():
      f.write(str(result[k]) + "," + str(k))
      f.write('\n')
    f.close

    D = result
    plt.bar(range(len(D)), D.values(), align='center')

    #plt.hist(latency, bins=bins)
    plt.title('Read your write consistency')
    plt.xlabel('Issuing Latency L(time unit)')
    plt.ylabel('Prob. of satisfying RYW')
    plt.show()

if __name__ == "__main__": main()
