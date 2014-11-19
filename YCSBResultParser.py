import sys
import re
from collections import namedtuple
import hashlib

def parse(s):
  pattern = '.*(UPDATE|READ).*key=(.*),\svalue=(Good|Mismatched)*(.*),\sst=(.*),\sen=(.*)'
  m = re.match(pattern, s)
  if m:
    op, key, readStatus, value, st, en =  m.groups()
    st, en  = int(st), int(en)
    isRead = op == 'READ'
    IsGoodRead = readStatus == 'Good'
    value = hashlib.md5(value).hexdigest()
    return isRead, key, value, IsGoodRead, st, en
  else:
    return None

def main(filename):
  Read = namedtuple("Read", ["Value", "Timestamp", "en", "IsGood"])
  Write = namedtuple("Write" , ["Value", "Timestamp", "en"])

  with open(filename) as f:
    content = f.readlines()

  readCnt, goodReadCnt, writeCnt = 0, 0, 0
  reads, writes = {}, {}
  for line in content:
    parsed = parse(line)
    if parsed:
      isRead, key, value, IsGoodRead, st, en = parse(line)
      if isRead:
        if key not in reads:
          reads[key] = []
        reads[key].append( Read(value, st, en, IsGoodRead) )
        if IsGoodRead:
          goodReadCnt += 1
      else:
        if key not in writes:
          writes[key] = []
        writes[key].append( Write(value, st, en) )
    else:
      print "ERROR parsing: %s" % line
      return 1

  reads = {k : sorted(reads[k], key=lambda x: x.Timestamp) for k in reads}
  writes = {k : sorted(writes[k], key=lambda x: x.Timestamp) for k in writes}

  freshRead, totalRead = 0, 0
  result = {}
  RESOLUTION = 0.01
  for key in reads:
    readList, writeList, i = reads[key], writes.get(key, []), 0
    writeMap = {w.Value: w for w in writeList}
    for read in reads[key]:
      while (i < len(writeList) and writeList[i].Timestamp <= read.Timestamp):
        i += 1
      if i==0: # ignore read that has latest write in the YCSB load phase
        continue
      latestWrite = writeList[i-1]
      thisWrite = writeMap.get(read.Value, None)
      timeDiff = (read.Timestamp - latestWrite.Timestamp) / 10E6
      isFresh = (latestWrite.Value == read.Value) or (thisWrite and thisWrite.Timestamp > read.Timestamp)

      freshRead += 1 if isFresh else 0
      totalRead += 1

      idx = int(timeDiff / RESOLUTION)
      if idx not in result:
        result[idx] = dict(freshRead=0, totalRead=0, freshGoodRead=0, totalGoodRead=0)
      result[idx]['freshRead'] += 1 if isFresh else 0
      result[idx]['totalRead'] += 1
      result[idx]['freshGoodRead'] += 1 if isFresh and read.IsGood else 0
      result[idx]['totalGoodRead'] += 1 if read.IsGood else 0

  for idx, res in result.iteritems():
    timeDiff = idx*RESOLUTION
    goodRatio = res['freshGoodRead']/float(res['totalGoodRead']) if res['totalGoodRead'] > 0 else None
    print timeDiff, res['freshRead']/float(res['totalRead']), res['freshRead'], res['totalRead'], \
          goodRatio, res['freshGoodRead'], res['totalGoodRead']
  print "freshRead=%s, totalRead=%s, ratio=%s" % (freshRead, totalRead, freshRead/float(totalRead))

if __name__ == '__main__':
  filename = sys.argv[1]
  main(filename)
