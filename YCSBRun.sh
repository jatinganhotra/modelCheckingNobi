#!/bin/bash

YCSB_HOME=/scratch/Confluence/modelCheckingYCSB/YCSB

usage()
{
  echo "usage: $1 -h hosts [-l (load data) | -t (run test) rate (operations/s)]"
  exit -1
}

load()
{
  echo "Load"

  echo $hosts
  ssh sonnbc@node-00.riak.confluence.emulab.net -C "
    java -cp $YCSB_HOME/core/target/*:$YCSB_HOME/lib/*:$YCSB_HOME/cassandra/target/cassandra-binding-0.1.4.jar \
    com.yahoo.ycsb.Client -load -db com.yahoo.ycsb.db.CassandraClient10 \
    -p cassandra.writeconsistencylevel=QUORUM -p cassandra.readconsistencylevel=QUORUM \
    -P $YCSB_HOME/workloads/modelCheckingWorkload -threads 10\
    -p hosts=\"$hosts\"
  "
}

run_test()
{
  echo "Run test"

  ssh sonnbc@node-00.riak.confluence.emulab.net -C "
    java -cp $YCSB_HOME/core/target/*:$YCSB_HOME/lib/*:$YCSB_HOME/cassandra/target/cassandra-binding-0.1.4.jar \
    com.yahoo.ycsb.Client -t -db com.yahoo.ycsb.db.CassandraClient10 \
    -p cassandra.writeconsistencylevel=ALL -p cassandra.readconsistencylevel=ALL \
    -P $YCSB_HOME/workloads/modelCheckingWorkload -target $rate\
    -p hosts=\"$hosts\"
  " 2>&1
}

while getopts "lt:h:" opt; do
  case "$opt" in
    l) action='load';;
    t) action='run_test';rate=$OPTARG;;
    h) hosts=$OPTARG;;
  esac
done

if [ -z "$action" ] || [ -z "$hosts" ]; then
    usage $0
fi

$action
