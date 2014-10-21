#!/bin/bash
# Given the number of nodes N, set up the Cassandra cluster using nodes from 1 to N

CASSANDRA_HOME=/modelCheckingCassandra
SYNC_POINT_CASSANDRA=/scratch/Confluence/modelCheckingCassandra
SYNC_POINT_YCSB=/scratch/Confluence/modelCheckingYCSB
CASSANDRA_DATA=/var/lib/cassandra
CASSANDRA_LOG=/var/log/cassandra

usage()
{
  echo "usage: $1 -n numnode -b cassandraBranch [timestampBased | agnostic] [-d (deploy) | -u (update) recompile/reset/keep]"
  echo "recompile: recompile cassandra and YCSB and reset cluster"
  echo "reset: don't recompile the code but reset cluster (empty all data)"
  echo "keep: just git pull but do nothing else"
  exit -1
}

kill_cassandra()
{
  echo "Kill Cassandra $numnode"
  for (( i = 0; i < $numnode; i++)); do
    ssh -t sonnbc@node-0$i.riak.confluence.emulab.net -C "
      ps aux | grep cassandra | grep -v grep | awk '{print \$2}' | xargs -L1 kill
    " &
  done

  wait
}

init_single_node()
{
  ssh -t sonnbc@node-0$1.riak.confluence.emulab.net -C "
    sudo rm -rf $CASSANDRA_HOME;
    sudo cp -r $SYNC_POINT_CASSANDRA $CASSANDRA_HOME;
    sudo chown -R sonnbc: $CASSANDRA_HOME;
    sudo rm -rf $CASSANDRA_DATA;
    sudo mkdir -p $CASSANDRA_DATA;
    sudo chown -R sonnbc $CASSANDRA_DATA;
    sudo rm -rf $CASSANDRA_LOG;
    sudo mkdir -p $CASSANDRA_LOG;
    sudo chown -R sonnbc $CASSANDRA_LOG;
    export listen_ip=\$(ifconfig | grep 10\.1\.1 | tr ':' ' ' | awk '{print \$3}');
    sudo sed -i -e \"s/localhost/\$listen_ip/g\" $CASSANDRA_HOME/conf/cassandra.yaml;
  "
}

start_cluster()
{
  echo "Setup $numnode"
  kill_cassandra

  for (( i = 0; i < $numnode; i++)); do
    init_single_node $i &
  done

  wait

  #start other nodes
  for (( i = 0; i < $numnode; i++)); do
    ssh -t sonnbc@node-0$i.riak.confluence.emulab.net -C "export $CASSANDRA_INCLUDE=$CASSANDRA_HOME/bin/cassandra.in.sh; $CASSANDRA_HOME/bin/cassandra; sleep 15;" &
  done

  wait

}

deploy()
{
  echo "Deploy $numnode"

  ssh -t sonnbc@node-00.riak.confluence.emulab.net -C "
    sudo rm -rf $SYNC_POINT_CASSANDRA;
    sudo rm -rf $SYNC_POINT_YCSB;
    git clone git@github.com:Sonnbc/modelCheckingCassandra.git $SYNC_POINT_CASSANDRA;
    git clone git@github.com:Sonnbc/modelCheckingNobi.git $SYNC_POINT_YCSB;
    cd $SYNC_POINT_YCSB/YCSB;
    mvn clean install -fae;
    cd $SYNC_POINT_CASSANDRA;
    ant;
  "
  start_cluster
}

update()
{
  echo "Update $numnode"

  if [ $update_opt = "recompile" ]; then
    recompile="
      cd $SYNC_POINT_YCSB/YCSB;
      mvn clean install -fae;
      cd $SYNC_POINT_CASSANDRA;
      ant;
    "
  fi

  ssh -t sonnbc@node-00.riak.confluence.emulab.net -C "
    cd $SYNC_POINT_YCSB;
    git pull;
    cd $SYNC_POINT_CASSANDRA;
    git fetch;
    git checkout -b cassandra_branch;
    git pull;
    $recompile
  "

  if [ $update_opt = "recompile" ] || [ $update_opt = "reset" ]; then
    start_cluster
  fi
}

while getopts "du:n:b:" opt; do
  case "$opt" in
    d) action='deploy';;
    u) action='update'; update_opt==$OPTARG;;
    n) numnode=$OPTARG;;
    b) cassandra_branch=$OPTARG;;
  esac
done


if [ -z "$numnode" ] || [ -z "$action" ] || [ -z $cassandra_branch ]; then
    usage $0
fi

$action
