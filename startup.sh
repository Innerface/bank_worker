#!/bin/sh
# change permission
chmod -R 755 ibm-*.jar
# start service
nohup java -jar ibm-eureka-0.0.1-SNAPSHOT.jar >./logs/eureka.log 2>&1 &
nohup java -jar ibm-admin-gateway-0.0.1-SNAPSHOT.jar >./logs/admin_gateway.log 2>&1 &
nohup java -jar ibm-m-gateway-0.0.1-SNAPSHOT.jar >./logs/m_gateway.log 2>&1 &
nohup java -jar ibm-server-api-0.0.1-SNAPSHOT.jar >./logs/server_api.log 2>&1 &
nohup java -jar ibm-web-admin-0.0.1-SNAPSHOT.jar >./logs/web_admin.log 2>&1 &
nohup java -jar ibm-server-xiaom-1.0-SNAPSHOT.jar >./logs/xiaom.log 2>&1 &
nohup java -jar ibm-service-model-0.0.1-SNAPSHOT.jar >./logs/model.log 2>&1 &
ps -ef |grep ibm
