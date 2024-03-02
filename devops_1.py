import boto3
import webbrowser
import time
import datetime
import json
import random
import string
import subprocess

ec2 = boto3.resource('ec2')
s = [] # the list of instance names

current_time = datetime.datetime.now()

formatted_time = current_time.strftime('%Y-%m-%d-%H-%M-%S') # formatting the date time string

print ("All instances:")
for inst in ec2.instances.all():

# list of all the current instances:
    print (inst.id, inst.state)
            
new_instance_name = f'Demo instance {formatted_time}' # gives the new instance an auto-incremented name

            
new_instances = ec2.create_instances(
    ImageId='ami-0277155c3f0ab2930',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.nano',
    SecurityGroupIds=[ 'sg-02f06ee823b64fc67' ], # security group
    TagSpecifications=[ # tag: instance name
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': new_instance_name,
                },
            ]
        },
    ],
    
    #user data to create apache web server
    UserData="""#!/bin/bash
            yum update -y
            yum install httpd -y
            systemctl enable httpd
            systemctl start httpd
            echo '<html>' > index.html
            echo '<body>' >> index.html
            TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
            echo '<h1>Welcome to DevOps, HDip CS 2024</h1><br>' >> index.html
            echo '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Devops-toolchain.svg/640px-Devops-toolchain.svg.png" alt="Dev Ops Image">' >> index.html
            echo '<h2>See instance metadata below: </h2><br>' >> index.html
            echo '<p>Private IP Address: </p>' >> index.html
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/local-ipv4) >> index.html
            echo '<br><p>availability zone: </p>' >> index.html
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/placement/availability-zone) >> index.html
            echo 'Instance Type: '
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://latest/meta-data/instance-type) >> index.html
            echo '<br><p>Public IP Address: </p>' >> index.html
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/public-ipv4) >> index.html
            echo '<br><p>AMI ID: </p>' >> index.html
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/ami-id) >> index.html
            echo '<br><p>Security Groups: </p>' >> index.html
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/security-groups) >> index.html
            echo '</body>' >> index.html
            cp index.html /var/www/html/index.html
            """,
    KeyName='HDip-2024'
    )

instance = new_instances[0]
    
print (f'Your New EC2 instance id is: {instance.id}')
print (f'Your new EC2 instance name is {new_instance_name}')
# uses waiter method to wait until the instance is in running state
print ("Instance Pending, please wait... ")
instance.wait_until_running()
print ("Instance Running")
instance.reload()
ip_address = instance.public_ip_address

print(f"The IP address of this instance is: {ip_address}")
print("Waiting for your apache web page to become available...")
time.sleep(30)
print("""
   _________________________________________
   
   ---------Opening EC2 Web page...---------
   _________________________________________
   
   """)    
webbrowser.open_new_tab(f"http://{ip_address}")

# create an s3 bucket
s3 = boto3.resource("s3")
s3client = boto3.client("s3")

def get_random_string(length):
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

bucket_id_string = get_random_string(6)

bucket_name = f'ccostello-{bucket_id_string}' # unique bucket name with 6 random chars

# create new bucket 
try:
    response = s3.create_bucket(Bucket=bucket_name)
    print(response)
except Exception as error:
    print(error)

s3client.delete_public_access_block(Bucket=bucket_name)
# set public read access - bucket policy
bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
                ]
}
s3.Bucket(bucket_name).Policy().put(Policy=json.dumps(bucket_policy)) 

# command to save image to local machine and redirect output to dev/null
command = "curl -o logo.jpg http://devops.witdemo.net/logo.jpg"

subprocess.run(command, shell=True)

image_object_name = 'logo.jpg'

# upload image 
try:
    response = s3.Object(bucket_name, image_object_name).put(Body=open(image_object_name, 'rb'),ContentType='image.jpeg')
    print (response)
except Exception as error:
    print (error)

# creating html content
html_content = f"""
<html>
    <body>
        <h1>Welcome to S3 Bucket Index Page</h1>
        <img src="https://{bucket_name}.s3.amazonaws.com/{image_object_name}" alt="SETU logo">
    </body>
</html>
"""

# put index.html in an s3 bucket
object_name = 'index.html'

try:
    response = s3.Object(bucket_name, object_name).put(Key='index.html',Body= html_content,ContentType='text/html')
    print (response)
except Exception as error:
    print (error)
   
website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'},
}

bucket_website = s3.BucketWebsite(f'{bucket_name}')   

bucket_website.put(WebsiteConfiguration=website_configuration)
print(f"bucket name: {bucket_name}")
print("""
   _________________________________________
   
   ------Opening S3 Bucket Endpoint...------
   _________________________________________
   
   """)
webbrowser.open_new_tab(f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com") # opens the s3 bucket endpoint

# monitoring
# script string run as command to run the monitoring shell script within the ec2 instance
monitoring_script = f"""scp -o StrictHostKeyChecking=no -i HDip-2024.pem monitoring.sh ec2-user@{ip_address}:. &&
    ssh -o StrictHostKeyChecking=no -i HDip-2024.pem ec2-user@{ip_address} 'chmod 700 monitoring.sh' &&
    ssh -o StrictHostKeyChecking=no -i HDip-2024.pem ec2-user@{ip_address} './monitoring.sh'"""
    
subprocess.run(monitoring_script, shell=True)

## cloudwatch - additional functionality

# List all running instance IDs
print("Running instances:")
for inst in ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]):
    print(inst.id)

print(f"Newly Created Instance: {new_instances[0].id}")
cloudwatch = boto3.resource('cloudwatch')
ec2 = boto3.resource('ec2')

instid = input("Please enter instance ID: ")    # Prompt the user to enter an Instance ID
print("Please wait while collecting data on CPU utilisation...")
instance = ec2.Instance(instid)
instance.monitor()  # Enables detailed monitoring on instance (1-minute intervals)

interval = 360

time.sleep(interval)     

metric_iterator = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                            MetricName='CPUUtilization',
                                            Dimensions=[{'Name':'InstanceId', 'Value': instid}])

metric = list(metric_iterator)[0]    # extract first (only) element

response = metric.get_statistics(StartTime = datetime.datetime.utcnow() - datetime.timedelta(minutes=5),   # 5 minutes ago # appended datetime class
                                 EndTime=datetime.datetime.utcnow(),                              # now # appended datetime class
                                 Period=300,                                             # 5 min intervals
                                 Statistics=['Average'])

print ("Average CPU utilisation:", response['Datapoints'][0]['Average'], response['Datapoints'][0]['Unit'])
# print (response)   # for debugging only

