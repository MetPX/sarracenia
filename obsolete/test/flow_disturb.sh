#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# linux only ...
# iprout2 should be installed by default ... if not :
# apt-get install iproute2 
#
# tc (traffic control)
#
# netem : provides Network Emulation functionality for testing protocols by emulating the properties
# of wide area networks. The current version emulates variable delay, loss, duplication and re-ordering. 

export FIRST=0

export DEV=${1}


# add interface for incoming traffic

function add_interface_to_incoming {
   modprobe ifb
   ip link set dev ifb0 up
   tc qdisc add dev ${1} ingress
   tc filter add dev ${1}  parent ffff: protocol ip u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev ifb0
}

# delete interface for incoming traffic

function del_interface_to_incoming {
   tc filter delete dev ${1} parent ffff: protocol ip u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev ifb0
   tc qdisc  delete dev ${1} ingress
   ip link set dev ifb0 down
   modprobe -r ifb
}

# when setting problem do on dev and incoming dev

function IO-tc {
   action=$1
   shift
   echo tc qdisc ${action} dev ${DEV} root netem $*
   echo tc qdisc ${action} dev  ifb0  root netem $*
}


# prepare incoming device

incoming_to_dev

# setup each problem sleeping $1 secs in between


# IO - delays : 100ms ± 10ms  

IO-tc add    delay 100ms 10ms
sleep ${2}
IO-tc delete delay 100ms 10ms

# IO - packets lost : 3% and each successive probability depends by 25% on the last one.     

IO-tc add    loss 0.3% 25%
sleep ${2}
IO-tc delete loss 0.3% 25%


# packets duplicated  

IO-tc add    duplicate 1%
sleep ${2}
IO-tc delete duplicate 1%

# packets currupted  

IO-tc add    corrupt 0.1%
sleep ${2}
IO-tc delete corrupt 0.1%

# packets reordering

IO-tc add    delay 10ms reorder 25% 50%
sleep ${2}
IO-tc delete delay 10ms reorder 25% 50%
