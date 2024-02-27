import boto3
ec2 = boto3.resource('ec2')
s = [] # the list of instance names
for inst in ec2.instances.all():
    instance_name = None
    if inst.tags is not None: # if the instance has a tag or not
        for tag in inst.tags:
            if tag['Key'] == 'Name': 
                instance_name = tag['Value']
                s.append(instance_name) # append the name to the list of names
                
    if instance_name is None:
        print(f"Instance {inst.id} doesn't have a name") # will let you know if there is an instance without a name

max_digit = 0            
for name in s:
    if name[-1].isdigit(): # check if the last character in the name is a digit
        digit = int(name[-1]) # convert string to int
        max_digit = max(max_digit, digit) # sets the maximum digit
            
new_instance_name = f'Demo instance {max_digit +1}' # gives the new instance an auto-incremented name
            
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
            systemctl start httpd""",
    KeyName='HDip-2024'
    )
    
print (new_instances[0].id)

