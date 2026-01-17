"""
AWS Cost Optimizer - Stop Resources Lambda
Stops EC2, RDS, ECS, DocumentDB, and Aurora resources based on tags
"""
import boto3
import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
ec2 = boto3.client('ec2')
rds = boto3.client('rds')
ecs = boto3.client('ecs')
docdb = boto3.client('docdb')

def get_tagged_resources(tag_key, tag_values):
    """Get resources with specific tags"""
    resources = {
        'ec2': [],
        'rds': [],
        'ecs': [],
        'docdb': [],
        'aurora': []
    }

    # EC2 Instances
    try:
        response = ec2.describe_instances(
            Filters=[
                {'Name': f'tag:{tag_key}', 'Values': tag_values},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                resources['ec2'].append(instance['InstanceId'])
    except Exception as e:
        logger.error(f"Error getting EC2 instances: {e}")

    # RDS Instances
    try:
        response = rds.describe_db_instances()
        for db in response['DBInstances']:
            if db['DBInstanceStatus'] == 'available':
                tags = rds.list_tags_for_resource(ResourceName=db['DBInstanceArn'])
                for tag in tags['TagList']:
                    if tag['Key'] == tag_key and tag['Value'] in tag_values:
                        if 'DBClusterIdentifier' not in db:  # Not part of Aurora
                            resources['rds'].append(db['DBInstanceIdentifier'])
    except Exception as e:
        logger.error(f"Error getting RDS instances: {e}")

    # Aurora Clusters
    try:
        response = rds.describe_db_clusters()
        for cluster in response['DBClusters']:
            if cluster['Status'] == 'available':
                tags = rds.list_tags_for_resource(ResourceName=cluster['DBClusterArn'])
                for tag in tags['TagList']:
                    if tag['Key'] == tag_key and tag['Value'] in tag_values:
                        resources['aurora'].append(cluster['DBClusterIdentifier'])
    except Exception as e:
        logger.error(f"Error getting Aurora clusters: {e}")

    # DocumentDB Clusters
    try:
        response = docdb.describe_db_clusters()
        for cluster in response['DBClusters']:
            if cluster['Status'] == 'available':
                tags = docdb.list_tags_for_resource(ResourceName=cluster['DBClusterArn'])
                for tag in tags['TagList']:
                    if tag['Key'] == tag_key and tag['Value'] in tag_values:
                        resources['docdb'].append(cluster['DBClusterIdentifier'])
    except Exception as e:
        logger.error(f"Error getting DocumentDB clusters: {e}")

    # ECS Services
    try:
        clusters = ecs.list_clusters()['clusterArns']
        for cluster_arn in clusters:
            services = ecs.list_services(cluster=cluster_arn)['serviceArns']
            for service_arn in services:
                service_desc = ecs.describe_services(cluster=cluster_arn, services=[service_arn])
                for svc in service_desc['services']:
                    if svc['desiredCount'] > 0:
                        tags = ecs.list_tags_for_resource(resourceArn=service_arn)
                        for tag in tags.get('tags', []):
                            if tag['key'] == tag_key and tag['value'] in tag_values:
                                resources['ecs'].append({
                                    'cluster': cluster_arn,
                                    'service': svc['serviceName'],
                                    'desiredCount': svc['desiredCount']
                                })
    except Exception as e:
        logger.error(f"Error getting ECS services: {e}")

    return resources

def stop_ec2_instances(instance_ids):
    """Stop EC2 instances"""
    if not instance_ids:
        return []

    stopped = []
    try:
        ec2.stop_instances(InstanceIds=instance_ids)
        stopped = instance_ids
        logger.info(f"Stopped EC2 instances: {instance_ids}")
    except Exception as e:
        logger.error(f"Error stopping EC2 instances: {e}")
    return stopped

def stop_rds_instances(db_identifiers):
    """Stop RDS instances"""
    stopped = []
    for db_id in db_identifiers:
        try:
            rds.stop_db_instance(DBInstanceIdentifier=db_id)
            stopped.append(db_id)
            logger.info(f"Stopped RDS instance: {db_id}")
        except Exception as e:
            logger.error(f"Error stopping RDS instance {db_id}: {e}")
    return stopped

def stop_aurora_clusters(cluster_identifiers):
    """Stop Aurora clusters"""
    stopped = []
    for cluster_id in cluster_identifiers:
        try:
            rds.stop_db_cluster(DBClusterIdentifier=cluster_id)
            stopped.append(cluster_id)
            logger.info(f"Stopped Aurora cluster: {cluster_id}")
        except Exception as e:
            logger.error(f"Error stopping Aurora cluster {cluster_id}: {e}")
    return stopped

def stop_docdb_clusters(cluster_identifiers):
    """Stop DocumentDB clusters"""
    stopped = []
    for cluster_id in cluster_identifiers:
        try:
            docdb.stop_db_cluster(DBClusterIdentifier=cluster_id)
            stopped.append(cluster_id)
            logger.info(f"Stopped DocumentDB cluster: {cluster_id}")
        except Exception as e:
            logger.error(f"Error stopping DocumentDB cluster {cluster_id}: {e}")
    return stopped

def stop_ecs_services(services):
    """Scale ECS services to 0"""
    stopped = []
    for svc in services:
        try:
            # Store original desired count in tags for restoration
            ecs.tag_resource(
                resourceArn=f"arn:aws:ecs:{boto3.session.Session().region_name}:{boto3.client('sts').get_caller_identity()['Account']}:service/{svc['cluster'].split('/')[-1]}/{svc['service']}",
                tags=[{'key': 'OriginalDesiredCount', 'value': str(svc['desiredCount'])}]
            )
            ecs.update_service(
                cluster=svc['cluster'],
                service=svc['service'],
                desiredCount=0
            )
            stopped.append(svc['service'])
            logger.info(f"Scaled ECS service to 0: {svc['service']}")
        except Exception as e:
            logger.error(f"Error stopping ECS service {svc['service']}: {e}")
    return stopped

def lambda_handler(event, context):
    """Main Lambda handler"""
    logger.info(f"Event: {json.dumps(event)}")

    tag_key = event.get('tag_key', 'Environment')
    tag_values = event.get('tag_values', ['dev', 'homolog', 'staging'])

    logger.info(f"Looking for resources with tag {tag_key}={tag_values}")

    # Get resources
    resources = get_tagged_resources(tag_key, tag_values)

    logger.info(f"Found resources: {json.dumps(resources, default=str)}")

    # Stop resources
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': 'stop',
        'tag_key': tag_key,
        'tag_values': tag_values,
        'stopped': {
            'ec2': stop_ec2_instances(resources['ec2']),
            'rds': stop_rds_instances(resources['rds']),
            'aurora': stop_aurora_clusters(resources['aurora']),
            'docdb': stop_docdb_clusters(resources['docdb']),
            'ecs': stop_ecs_services(resources['ecs'])
        }
    }

    logger.info(f"Results: {json.dumps(results)}")

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
