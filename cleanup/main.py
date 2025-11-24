import boto3
from botocore.exceptions import ClientError
import os

EC2_CLIENT = boto3.client(
    "ec2",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"), 
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
)

def terminate_ec2_instances():
    print("Starting process to terminate EC2 instances...")
    try:
        response = EC2_CLIENT.describe_instances()
        instance_ids_to_delete = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                if instance["State"]["Name"] == "running":
                    instance_ids_to_delete.append(instance["InstanceId"])

        if instance_ids_to_delete:
            EC2_CLIENT.terminate_instances(InstanceIds=instance_ids_to_delete)
            waiter = EC2_CLIENT.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=instance_ids_to_delete)

        print("Termination process for EC2 instances is done")
    except ClientError as e:
        print(f"Failed to terminate EC2 instances:{e}")
        raise RuntimeError("Failed to terminate EC2 instances") from e

def terminate_security_groups():
    print("Starting process to delete security groups...")
    try:
        sg_names_in_order = ["mysql-manager-sg", "mysql-worker-sg", "proxy-sg", "gatekeeper-sg"]
        
        response = EC2_CLIENT.describe_security_groups()
        
        for sg_name in sg_names_in_order:
            for sg in response["SecurityGroups"]:
                if sg["GroupName"] == sg_name:
                    try:
                        EC2_CLIENT.delete_security_group(GroupId=sg["GroupId"])
                    except Exception as e:
                        print(f"Failed to delete {sg_name} ({sg['GroupId']}): {e}")
                    break

        print("Deletion process for security groups is done")
    except ClientError as e:
        print(f"Failed to delete security groups:{e}")
        raise RuntimeError("Failed to delete security groups") from e

def main():
    terminate_ec2_instances()
    terminate_security_groups()

if __name__ == "__main__":
    main()
