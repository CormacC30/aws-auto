import boto3
import webbrowser
import time
import datetime
import json
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
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html)
            echo '<br><p>availability zone: </p>' >> index.html
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/placement/availability-zone >> index.html)
            echo 'Instance Type: '
            echo $(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://latest/meta-data/instance-type >> index.html)
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
webbrowser.open_new_tab(f"http://{ip_address}")

# create an s3 bucket
s3 = boto3.resource("s3")
s3client = boto3.client("s3")

new_bucket_name = f'demo-aws-bucket-{formatted_time}' # unique bucket name with the current date time,

try:
    response = s3.create_bucket(Bucket=new_bucket_name)
    print(response)
except Exception as error:
    print(error)

s3client.delete_public_access_block(Bucket=new_bucket_name)
# set public read access - bucket policy
bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": f"arn:aws:s3:::{new_bucket_name}/*"
                }
                ]
}
s3.Bucket(new_bucket_name).Policy().put(Policy=json.dumps(bucket_policy)) 
   
website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'},
}

bucket_website = s3.BucketWebsite(f'{new_bucket_name}')   

bucket_website.put(WebsiteConfiguration=website_configuration)
print(f"bucket name: {new_bucket_name}")
print("Upload an index.html file to test it works!")

cmd = f"scp -o StrictHostKeyChecking=no -i ~/DevOps/HDip-2024.pem ec2-user@{ip_address}:/var/www/html/index.html ."

result = subprocess.run(cmd, shell=True)
print (result.returncode)
# put index.html in an s3 bucket

object_name = 'index.html'

try:
    response = s3.Object(new_bucket_name, object_name).put(Body=open(object_name, 'rb'),ContentType='text/html')
    print (response)
except Exception as error:
    print (error)

# retrieve and upload the test image to the s3 bucket


# command to save image to local machine and redirect output to dev/null
command = "curl -o logo.jpg http://devops.witdemo.net/logo.jpg 1> /dev/null "

subprocess.run(command, shell=True)

image_object_name = 'logo.jpg'

try:
    response = s3.Object(new_bucket_name, image_object_name).put(Body=open(image_object_name, 'rb'),ContentType='image.jpeg')
    print (response)
except Exception as error:
    print (error)
