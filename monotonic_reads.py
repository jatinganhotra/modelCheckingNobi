import sys
import re
from collections import namedtuple
import hashlib
import pprint

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

def get_c2_reads_after_this_read(c2r, rt):
    c2_reads_after_this_timestamp = []
    for read in c2r:
      if( read.Timestamp > rt):
        c2_reads_after_this_timestamp.append(read)
    return c2_reads_after_this_timestamp

# There is another write from c1 or c2 between latest and next, then ignore these cases
def isWriteBetweenLatestAndNext(w, c2w, latest, next):
    for write in c2w:
      if( write.Timestamp > latest and write.Timestamp < next):
        return True, write

    for write in w:
      if( write.Timestamp > latest and write.Timestamp < next):
        return True, write

    return False, None

def main(filename1, filename2):
  Read = namedtuple("Read", ["Value", "Timestamp", "IsGood", "ThreadID", "end"])
  Write = namedtuple("Write" , ["Value", "Timestamp", "ThreadID", "end"])
  Good = namedtuple("Good", ["Value", "latency"])
  Bad = namedtuple("Bad", ["Value", "latency"])

  f = open("c1-logs", "w+")

  with open(filename1) as f2:
    content = f2.readlines()
  reads, writes = {}, {}
  r , w = [], []
  for line in content:
    parsed = parse(line)
    if parsed:
      threadID, isRead, key, value, IsGoodRead, st, end = parse(line)
      if isRead:
        if key not in reads:
          reads[key] = []
        reads[key].append( Read(value, st, IsGoodRead, threadID, end) )
        r.append( Read(value, st, IsGoodRead, threadID, end) )
        f.write(str(Read(value, st, IsGoodRead, threadID, end)))
        f.write('\n')
      else:
        if key not in writes:
          writes[key] = []
        writes[key].append( Write(value, st, threadID, end) )
        w.append( Write(value, st, threadID, end) )
        f.write( str(Write(value, st, threadID, end) ))
        f.write('\n')
    else:
      continue
      #print "ERROR parsing: %s" % line
      #return 1

  f.close

  # Reading the second client file
  with open(filename2) as f:
    c2content = f.readlines()

  f = open("c2-logs", "w+")

  c2reads, c2writes = {}, {}
  c2r , c2w = [], []
  for line in c2content:
    parsed = parse(line)
    if parsed:
      threadID, isRead, key, value, IsGoodRead, st, end = parse(line)
      if isRead:
        if key not in c2reads:
          c2reads[key] = []
        c2reads[key].append( Read(value, st, IsGoodRead, threadID, end) )
        c2r.append( Read(value, st, IsGoodRead, threadID, end) )
        f.write(str(Read(value, st, IsGoodRead, threadID, end)))
        f.write('\n')
      else:
        if key not in c2writes:
          c2writes[key] = []
        c2writes[key].append( Write(value, st, threadID, end) )
        c2w.append( Write(value, st, threadID, end) )
        f.write( str(Write(value, st, threadID, end) ))
        f.write('\n')
    else:
      continue
      #print "ERROR parsing: %s" % line
      #return 1
  f.close

  # ------------------Reading the c2 client file ends here-------------

  r.sort(key=lambda x: x.end)
  good_reads = []
  all_reads = []
  gcount = 0
  acount = 0
  bcount = 0
  missed_cases = 0
  count = 0

  for key in w:
    # count = count + 1
    # if (count > 100):
    #     break;
    rt = key.Timestamp

    # Get the next 2 reads on client 2 after this write
    c2_reads_after_this_timestamp = get_c2_reads_after_this_read(c2r, rt)
    # Sort the reads before based on their Timestamp
    c2_reads_after_this_timestamp.sort(key=lambda x: x.Timestamp)

    if (len(c2_reads_after_this_timestamp) == 0):
      missed_cases = missed_cases + 1
      continue

    latest = c2_reads_after_this_timestamp[0]
    next = c2_reads_after_this_timestamp[1]

    # There is another write from c1 or c2 between latest and next, then ignore these cases
    is_true, middle_write = isWriteBetweenLatestAndNext(w, c2w, latest.Timestamp, next.Timestamp)
    if ( is_true ):
        # print "Missed case - monotonic read"
        # print str("Latest       ") + str(latest.Value) + " " + str(latest.Timestamp) + " " + str(latest.end)
        # print str("Middle write ") + str(middle_write.Value) + " " + str(middle_write.Timestamp) + " " + str(middle_write.end)
        # print str("Next         ") + str(next.Value) + " " + str(next.Timestamp) + " " + str(next.end)
        # print "------------------------------------------"
        missed_cases = missed_cases + 1
        continue

    if ( latest.Value != key.Value and ( next.Value == latest.Value or next.Value == key.Value ) ) or ( latest.Value == key.Value and next.Value == key.Value ):
        gcount = gcount + 1
        acount = acount + 1
        good_reads.append(Good(key.Value, key.Timestamp - latest.Timestamp))
        all_reads.append(Good(key.Value, key.Timestamp - latest.Timestamp))
    else:
        # print "Bad monotonic read"
        # print str("Key    ") + str(key.Value) + " " + str(key.Timestamp) + " " + str(key.end)
        # print str("Latest ") + str(latest.Value) + " " + str(latest.Timestamp) + " " + str(latest.end)
        # print str("Next   ") + str(next.Value) + " " + str(next.Timestamp) + " " + str(next.end)
        # print "------------------------------------------"
        bcount = bcount + 1
        all_reads.append(Good(key.Value, key.Timestamp - latest.Timestamp))
        continue

  good_reads_sorted = []
  for k in good_reads:
    good_reads_sorted.append(abs(k.latency))
  good_reads_sorted.sort()
  f = open("good_reads", "w+")
  for k in good_reads_sorted:
      f.write(str(k))
      f.write('\n')
  f.close

  all_reads_sorted = []
  for k in all_reads:
      all_reads_sorted.append(abs(k.latency))
  all_reads_sorted.sort()
  f = open("all_reads", "w+")
  for k in all_reads_sorted:
      f.write(str(k))
      f.write('\n')
  f.close

  print "Total writes in c1 writes are - " + str(len(w))
  print "Size of good reads - " + str(len(good_reads))
  print "All reads are - " + str(len(r))
  print "gcount is = " + str(gcount)
  print "acount is = " + str(acount)
  print "bcount is = " + str(bcount)
  print "missed_cases is = " + str(missed_cases)

if __name__ == '__main__':
  filename1 = sys.argv[1]
  filename2 = sys.argv[2]
  main(filename1, filename2)
