import sys
import re

def parse(s):
  pattern = '.*(UPDATE|READ).*key=(.*),\svalue=(Good|Mismatched)*(.*),\sst=(.*),\sen=(.*)'
  m = re.match(pattern, s)
  if m:
    print m.groups()
    op, key, readStatus, value, st, en =  m.groups()
    st, en  = int(st), int(en)
    isRead = op == 'READ'
    isGoodRead = readStatus == 'Good'
    return isRead, key, value, isGoodRead, st, en
  else:
    return None

def main(filename):
  with open(filename) as f:
    content = f.readlines()
  for line in content:
    isRead, key, value, st, en, isGoodRead = parse(line)
    print isRead, key, value, st, en, isGoodRead

if __name__ == '__main__':
  #filename = sys.argv[1]
  #main(filename)
  print parse("[Thread-1] INFO com.yahoo.ycsb.DBWrapper - READ: key=user1000385178204227360, value=Good+.'!0#!?x3, st=1411361540298381000, en=1411361540299150000")
  print parse("[Thread-1] INFO com.yahoo.ycsb.DBWrapper - UPDATE: key=user8517097267634966620, value=  506)7%-(, st=1411361540300041000, en=1411361540300468000")
