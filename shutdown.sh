#!/bin/sh
# upload file to dir /data/webapp/deploy
#
#stop service
ps -ef|grep ibm-service-model|awk '{print $2}'|while read pid
do 
	kill -9 $pid
done

ps -ef|grep ibm-server-xiaom|awk '{print $2}'|while read pid
do 
	kill -9 $pid
done

ps -ef|grep ibm-web-admin|awk '{print $2}'|while read pid
do 
	kill -9 $pid
done

ps -ef|grep ibm-server-api|awk '{print $2}'|while read pid
do 
	kill -9 $pid
done

ps -ef|grep ibm-admin-gateway|awk '{print $2}'|while read pid
do 
	kill -9 $pid
done

ps -ef|grep ibm-m-gateway|awk '{print $2}'|while read pid
do 
	kill -9 $pid
done

ps -ef|grep ibm-eureka|awk '{print $2}'|while read pid
do 
	kill -9 $pid
done
