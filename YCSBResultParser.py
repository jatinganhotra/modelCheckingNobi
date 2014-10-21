import sys
import re
from collections import namedtuple

def parse(s):
  pattern = '.*(UPDATE|READ).*key=(.*),\svalue=(Good|Mismatched)*(.*),\sst=(.*),\sen=(.*)'
  m = re.match(pattern, s)
  if m:
    op, key, readStatus, value, st, en =  m.groups()
    st, en  = int(st), int(en)
    isRead = op == 'READ'
    isGoodRead = readStatus == 'Good'
    return isRead, key, value, isGoodRead, st, en
  else:
    return None

def main(filename):
  Read = namedtuple("Read", ["Value", "Timestamp", "IsGood"])
  Write = namedtuple("Write" , ["Value", "Timestamp"])

  with open(filename) as f:
    content = f.readlines()

  readCnt, goodReadCnt, writeCnt = 0, 0, 0
  reads, writes = {}, {}
  for line in content:
    parsed = parse(line)
    if parsed:
      isRead, key, value, isGoodRead, st, en = parse(line)
      if isRead:
        if key not in reads:
          reads[key] = []
        reads[key].append( Read(value, st, isGoodRead) )
        readCnt += 1
        if isGoodRead:
          goodReadCnt += 1
      else:
        if key not in writes:
          writes[key] = []
        writes[key].append( Write(value, st) )
        writeCnt += 1
    else:
      print "ERROR parsing: %s" % line
      return 1

  reads = {k : sorted(reads[k], key=lambda x: x.Timestamp) for k in reads}
  writes = {k : sorted(writes[k], key=lambda x: x.Timestamp) for k in writes}

  freshReadCnt, freshGoodReadCnt = 0, 0
  for key in reads:
    readList, writeList, i = reads[key], writes.get(key, []), 0
    for read in reads[key]:
      while (i < len(writeList) and writeList[i].Timestamp <= read.Timestamp):
        i += 1
      if (i==0 or writeList[i-1].Value == read.Value):
        freshReadCnt += 1
        if read.IsGood:
          freshGoodReadCnt +=1

  print "Total: read = %s, goodRead = %s, write = %s" % (readCnt, goodReadCnt, writeCnt)
  print "freshRead = %s/%s, ratio = %s" % (freshReadCnt, readCnt, freshReadCnt / float(readCnt))
  print "freshGoodRead = %s/%s, ratio = %s" % (
    freshGoodReadCnt, goodReadCnt, freshGoodReadCnt / float(goodReadCnt))

if __name__ == '__main__':
  filename = sys.argv[1]
  main(filename)
