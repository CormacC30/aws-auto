#!/usr/bin/bash
#
# Some basic monitoring functionality; Tested on Amazon Linux 2023.
#
TOKEN=`curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
MEMORYUSAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
PROCESSES=$(expr $(ps -A | grep -c .) - 1)
HTTPD_PROCESSES=$(ps -A | grep -c httpd)
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}') # cpu usage
CONNECTED=$(netstat | grep -c "CONNECTED") # connected interfaces
DISKUSAGE=$(df -h | awk '$NF == "/" { print $5 }') # disk usage

echo "Instance ID: $INSTANCE_ID"
echo
echo "------------------------------"
echo
echo "Memory utilisation: $MEMORYUSAGE"
echo
echo "------------------------------"
echo
echo "No of processes: $PROCESSES"
echo
echo "------------------------------"
echo
if [ $HTTPD_PROCESSES -ge 1 ]
then
    echo "Web server is running"
else
    echo "Web server is NOT running"
fi
echo
echo "------------------------------"
echo
echo "current CPU usage (%): $CPU"
echo
echo "------------------------------"
echo
echo "number of connected interfaces: $CONNECTED"
echo
echo "------------------------------"
echo
echo "disk usage: $DISKUSAGE"

