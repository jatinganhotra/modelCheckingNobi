#!/bin/bash
# Given the number of nodes N, set up the Cassandra cluster using nodes from 1 to N

PROJECT_HOME=/modelChecking
SYNC_POINT=/scratch/Confluence/modelChecking
CASSANDRA_DATA=/var/lib/cassandra
CASSANDRA_LOG=/var/log/cassandra

usage()
{
  echo "usage: $1 -n numnode [-d (deploy) | -u (update) recompile/reset/keep]"
  echo "recompile: recompile cassandra and YCSB and reset cluster"
  echo "reset: don't recompile the code but reset cluster"
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
    sudo rm -rf $PROJECT_HOME;
    sudo cp -r $SYNC_POINT $PROJECT_HOME;
    sudo chown -R sonnbc: $PROJECT_HOME;
    sudo rm -rf $CASSANDRA_DATA;
    sudo mkdir -p $CASSANDRA_DATA;
    sudo chown -R sonnbc $CASSANDRA_DATA;
    sudo rm -rf $CASSANDRA_LOG;
    sudo mkdir -p $CASSANDRA_LOG;
    sudo chown -R sonnbc $CASSANDRA_LOG;
    export listen_ip=\$(ifconfig | grep 10\.1\.1 | tr ':' ' ' | awk '{print \$3}');
    sudo sed -i -e \"s/localhost/\$listen_ip/g\" $PROJECT_HOME/cassandra/conf/cassandra.yaml;
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
    ssh -t sonnbc@node-0$i.riak.confluence.emulab.net -C "$PROJECT_HOME/cassandra/bin/cassandra; sleep 15;" &
  done

  wait

}

deploy()
{
  echo "Deploy $numnode"

  ssh -t sonnbc@node-00.riak.confluence.emulab.net -C "
    sudo rm -rf $SYNC_POINT;
    git clone git@github.com:Sonnbc/modelCheckingNobi.git $SYNC_POINT;
    cd $SYNC_POINT/YCSB;
    mvn clean install -fae;
    cd $SYNC_POINT/cassandra;
    ant;
  "
  start_cluster
}

update()
{
  echo "Update $numnode"

  if [ $update_opt = "recompile" ]; then
    recompile="
      cd $SYNC_POINT/YCSB;
      mvn clean install -fae;
      cd $SYNC_POINT/cassandra;
      ant;
    "
  fi

  ssh -t sonnbc@node-00.riak.confluence.emulab.net -C "
    cd $SYNC_POINT;
    git pull;
    $recompile
  "

  if [ $update_opt = "recompile" ] || [ $update_opt = "reset" ]; then
    start_cluster
  fi
}

while getopts "du:n:" opt; do
  case "$opt" in
    d) action='deploy';;
    u) action='update'; update_opt==$OPTARG;;
    n) numnode=$OPTARG;;
  esac
done


if [ -z "$numnode" ] || [ -z "$action" ]; then
    usage $0
fi

$action
