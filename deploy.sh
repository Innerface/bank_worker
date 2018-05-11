!/bin/sh
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

