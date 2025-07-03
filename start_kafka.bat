@echo off
echo Killing any stale Kafka/ZooKeeper Java processes...
taskkill /IM java.exe /F >nul 2>&1

echo Starting ZooKeeper...
start "ZooKeeper" cmd /c "bin\windows\zookeeper-server-start.bat config\zookeeper.properties"
timeout /t 5 /nobreak >nul

echo Deleting stale Kafka broker znode (if exists)...
echo delete /brokers/ids/0 | bin\windows\zookeeper-shell.bat localhost:2181 >nul 2>&1

echo Starting Kafka...
start "Kafka" cmd /c "bin\windows\kafka-server-start.bat config\server.properties"
timeout /t 5 /nobreak >nul

echo Starting Kafka Console Consumer...
start "Consumer" cmd /c "bin\windows\kafka-console-consumer.bat --bootstrap-server localhost:9092 --topic test --from-beginning"

pause
