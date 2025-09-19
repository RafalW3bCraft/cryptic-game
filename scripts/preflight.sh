#!/bin/bash
# block outbound from docker bridge (lab-net)
iptables -I DOCKER-USER -s 172.18.0.0/16 -j DROP
# verify
iptables -L DOCKER-USER -n --line-numbers
