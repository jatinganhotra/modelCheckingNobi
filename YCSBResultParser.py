import sys
import re
from collections import namedtuple
import hashlib

def parse(s):
  pattern = '\[Thread-(.*)\].*(UPDATE|READ).*key=(.*),\svalue=(Good|Mismatched)*(.*),\sst=(.*),\sen=(.*)'
  m = re.match(pattern, s)
  if m:
    threadID, op, key, readStatus, value, st, en =  m.groups()
    threadID, st, en  = int(threadID), int(st), int(en)
    isRead = op == 'READ'
    IsGoodRead = readStatus == 'Good'
    value = hashlib.md5(value).hexdigest()
    return threadID, isRead, key, value, IsGoodRead, st, en
  else:
    return None

def main(filename):
  Read = namedtuple("Read", ["Value", "Timestamp", "IsGood", "ThreadID"])
  Write = namedtuple("Write" , ["Value", "Timestamp", "ThreadID"])

  with open(filename) as f:
    content = f.readlines()

  reads, writes = {}, {}
  for line in content:
    parsed = parse(line)
    if parsed:
      threadID, isRead, key, value, IsGoodRead, st, en = parse(line)
      if isRead:
        if key not in reads:
          reads[key] = []
        reads[key].append( Read(value, st, IsGoodRead, threadID) )
      else:
        if key not in writes:
          writes[key] = []
        writes[key].append( Write(value, st, threadID) )
    else:
      print "ERROR parsing: %s" % line
      return 1

  #print reads
  #print writes
  print "Sorting the reads & writes based on timestamps"
  reads = {k : sorted(reads[k], key=lambda x: x.Timestamp) for k in reads}
  writes = {k : sorted(writes[k], key=lambda x: x.Timestamp) for k in writes}
  #print writes
  #print reads

  for key in reads:
    readList, writeList = reads[key], writes.get(key, [])
    #print readList
    #print writeList
    writeMap = {w.Value: w for w in writeList}
    #print "The writeMap is = " + str(writeMap)
    #print "--------------------"
    lastestResponses = {}
    staleRead = 0
    for read in readList:
      #print "Looking at read = " + str(read)
      write = writeMap.get(read.Value, None)
      #print "The write for the read value is = " + str(write)
      #print "Looking for read.ThreadID = " + str(read.ThreadID)
      latestWrite = lastestResponses.get(read.ThreadID, None)
      #print "Value for latestWrite " + str(latestWrite)
      if (latestWrite and write and write.Timestamp < latestWrite.Timestamp):
        print "-------------------------------------------"
        print " read is = " + str(read)
        print " latestWrite is - " + str(latestWrite)
        print " write is - " + str(write)
        print " write.Timestamp = " + str(write.Timestamp)
        print " latestWrite.Timestamp = " + str(latestWrite.Timestamp)
        staleRead += 1
      else:
        lastestResponses[read.ThreadID] = write
        #print lastestResponses
    #print "*********************************************"

    print "staleRead=%s/%s, totalWrite=%s" % (staleRead, len(readList), len(writeList))

if __name__ == '__main__':
  filename = sys.argv[1]
  main(filename)
