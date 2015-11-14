#!/bin/bash
# Given the number of nodes N, set up the Cassandra cluster using nodes from 1 to N

DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
USER=$(cat $DIR/account | grep USER | awk '{print $2}')
DOMAIN=$(cat $DIR/account | grep DOMAIN | awk {'print $2'})

ssh -t $USER@node-00.$DOMAIN -C "
x=\$(ifconfig | grep 10\.1\.1 | tr ':' ' ' | awk '{print \$3}');
  echo "The listen ip address is";
  echo \$x;
  "

ssh -t $USER@node-01.$DOMAIN -C "
x=\$(ifconfig | grep 10\.1\.1 | tr ':' ' ' | awk '{print \$3}');
  echo "The listen ip address is";
  echo \$x;
  "
ssh -t $USER@node-02.$DOMAIN -C "
x=\$(ifconfig | grep 10\.1\.1 | tr ':' ' ' | awk '{print \$3}');
  echo "The listen ip address is";
  echo \$x;
  "
ssh -t $USER@node-03.$DOMAIN -C "
x=\$(ifconfig | grep 10\.1\.1 | tr ':' ' ' | awk '{print \$3}');
  echo "The listen ip address is";
  echo \$x;
  "
