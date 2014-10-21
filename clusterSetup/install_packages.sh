N=$1

for ((i = 0; i < $N; i++)); do
  ssh -t sonnbc@node-0$i.riak.confluence.emulab.net -C "
    sudo apt-get update;
    sudo apt-get -y install openjdk-7-jdk;
    sudo apt-get -y install maven;
    sudo apt-get -y install ant;
    sudo apt-get -y install python-numpy
  " &
done

wait
