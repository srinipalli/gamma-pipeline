Data Pipeline

1.	Download and set up Fluentd - https://s3.amazonaws.com/packages.treasuredata.com/5/windows/fluent-package-5.2.0-x64.msi
•	Replace the fluentd.conf file in C:\opt\fluent\etc\fluent with the one from github
•	To start fluentd run cmd as admin and run “net start fluentdwinsvc”

2.	Kafka - https://dlcdn.apache.org/kafka/3.9.1/kafka-3.9.1-src.tgz
•	Extract the compressed file and rename the folder to kafka
•	Go to C:\kafka\config and replace zookeeper.properties and server.properties with the one from github
•	To start the kafka server and zookeeper save the start_kafka.bat file in kafka folder and run it.
