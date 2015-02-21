#!/bin/bash

YCSB_HOME=modelCheckingYCSB/YCSB

DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
USER=$(cat $DIR/clusterSetup/account | grep USER | awk '{print $2}')
DOMAIN=$(cat $DIR/clusterSetup/account | grep DOMAIN | awk {'print $2'})

usage()
{
  echo "usage: $1 -n numnode [-l (load data) | -t (run test)]"
  exit -1
}

get_hosts()
{
  hosts=$(
    for (( i = 0; i < $numnode; i++)); do
      ssh $USER@node-0$i.$DOMAIN -C "
        ifconfig | grep 10\.1\.1 | tr ':' ' ' | awk '{print \$3}'
      "
    done | tr "\\n" ",")
  echo $hosts
}

load()
{
  echo "Load $numnode"

  echo $hosts
  ssh $USER@node-00.$DOMAIN -C "
    java -cp $YCSB_HOME/core/target/*:$YCSB_HOME/lib/*:$YCSB_HOME/cassandra/target/cassandra-binding-0.1.4.jar \
    com.yahoo.ycsb.Client -load -db com.yahoo.ycsb.db.CassandraClient10 \
    -p cassandra.writeconsistencylevel=QUORUM -p cassandra.readconsistencylevel=QUORUM \
    -P $YCSB_HOME/workloads/modelCheckingWorkload -threads 1 -clientid 0 \
    -p hosts=\"$hosts\"
  "
}

run_test()
{
  echo "Run test $numnode"
    # Only read workload for clientid - 0
    ssh $USER@node-00.$DOMAIN -C "
      java -cp $YCSB_HOME/core/target/*:$YCSB_HOME/lib/*:$YCSB_HOME/cassandra/target/cassandra-binding-0.1.4.jar \
      com.yahoo.ycsb.Client -t -db com.yahoo.ycsb.db.CassandraClient10 \
      -p cassandra.writeconsistencylevel=ONE -p cassandra.readconsistencylevel=ONE \
      -P $YCSB_HOME/workloads/readworkload -threads 50 \
      -clientid 0 \
      -p hosts=\"$hosts\"
    " 2> node-00.log &
    # Only write workload for clientid - 1
    ssh $USER@node-01.$DOMAIN -C "
      java -cp $YCSB_HOME/core/target/*:$YCSB_HOME/lib/*:$YCSB_HOME/cassandra/target/cassandra-binding-0.1.4.jar \
      com.yahoo.ycsb.Client -t -db com.yahoo.ycsb.db.CassandraClient10 \
      -p cassandra.writeconsistencylevel=ONE -p cassandra.readconsistencylevel=ONE \
      -P $YCSB_HOME/workloads/writeworkload -threads 50 \
      -clientid 1 \
      -p hosts=\"$hosts\"
    " 2> node-01.log &

  wait

  cat node-0*.log
  #rm node-0*.log
}

while getopts "ltn:" opt; do
  case "$opt" in
    l) action='load';;
    t) action='run_test';;
    n) numnode=$OPTARG;;
  esac
done

if [ -z "$numnode" ] || [ -z "$action" ]; then
    usage $0
fi

hosts=$(get_hosts)

$action
