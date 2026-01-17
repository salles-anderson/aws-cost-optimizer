"""
AWS Cost Optimizer - Start Resources Lambda
Starts EC2, RDS, ECS, DocumentDB, and Aurora resources based on tags
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

def get_stopped_resources(tag_key, tag_values):
    """Get stopped resources with specific tags"""
    resources = {
        'ec2': [],
        'rds': [],
        'ecs': [],
        'docdb': [],
        'aurora': []
    }

    # EC2 Instances (stopped)
    try:
        response = ec2.describe_instances(
            Filters=[
                {'Name': f'tag:{tag_key}', 'Values': tag_values},
                {'Name': 'instance-state-name', 'Values': ['stopped']}
            ]
        )
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                resources['ec2'].append(instance['InstanceId'])
    except Exception as e:
        logger.error(f"Error getting EC2 instances: {e}")

    # RDS Instances (stopped)
    try:
        response = rds.describe_db_instances()
        for db in response['DBInstances']:
            if db['DBInstanceStatus'] == 'stopped':
                tags = rds.list_tags_for_resource(ResourceName=db['DBInstanceArn'])
                for tag in tags['TagList']:
                    if tag['Key'] == tag_key and tag['Value'] in tag_values:
                        if 'DBClusterIdentifier' not in db:
                            resources['rds'].append(db['DBInstanceIdentifier'])
    except Exception as e:
        logger.error(f"Error getting RDS instances: {e}")

    # Aurora Clusters (stopped)
    try:
        response = rds.describe_db_clusters()
        for cluster in response['DBClusters']:
            if cluster['Status'] == 'stopped':
                tags = rds.list_tags_for_resource(ResourceName=cluster['DBClusterArn'])
                for tag in tags['TagList']:
                    if tag['Key'] == tag_key and tag['Value'] in tag_values:
                        resources['aurora'].append(cluster['DBClusterIdentifier'])
    except Exception as e:
        logger.error(f"Error getting Aurora clusters: {e}")

    # DocumentDB Clusters (stopped)
    try:
        response = docdb.describe_db_clusters()
        for cluster in response['DBClusters']:
            if cluster['Status'] == 'stopped':
                tags = docdb.list_tags_for_resource(ResourceName=cluster['DBClusterArn'])
                for tag in tags['TagList']:
                    if tag['Key'] == tag_key and tag['Value'] in tag_values:
                        resources['docdb'].append(cluster['DBClusterIdentifier'])
    except Exception as e:
        logger.error(f"Error getting DocumentDB clusters: {e}")

    # ECS Services (scaled to 0)
    try:
        clusters = ecs.list_clusters()['clusterArns']
        for cluster_arn in clusters:
            services = ecs.list_services(cluster=cluster_arn)['serviceArns']
            for service_arn in services:
                service_desc = ecs.describe_services(cluster=cluster_arn, services=[service_arn])
                for svc in service_desc['services']:
                    if svc['desiredCount'] == 0:
                        tags = ecs.list_tags_for_resource(resourceArn=service_arn)
                        tag_dict = {t['key']: t['value'] for t in tags.get('tags', [])}
                        if tag_dict.get(tag_key) in tag_values:
                            original_count = int(tag_dict.get('OriginalDesiredCount', 1))
                            resources['ecs'].append({
                                'cluster': cluster_arn,
                                'service': svc['serviceName'],
                                'desiredCount': original_count
                            })
    except Exception as e:
        logger.error(f"Error getting ECS services: {e}")

    return resources

def start_ec2_instances(instance_ids):
    """Start EC2 instances"""
    if not instance_ids:
        return []

    started = []
    try:
        ec2.start_instances(InstanceIds=instance_ids)
        started = instance_ids
        logger.info(f"Started EC2 instances: {instance_ids}")
    except Exception as e:
        logger.error(f"Error starting EC2 instances: {e}")
    return started

def start_rds_instances(db_identifiers):
    """Start RDS instances"""
    started = []
    for db_id in db_identifiers:
        try:
            rds.start_db_instance(DBInstanceIdentifier=db_id)
            started.append(db_id)
            logger.info(f"Started RDS instance: {db_id}")
        except Exception as e:
            logger.error(f"Error starting RDS instance {db_id}: {e}")
    return started

def start_aurora_clusters(cluster_identifiers):
    """Start Aurora clusters"""
    started = []
    for cluster_id in cluster_identifiers:
        try:
            rds.start_db_cluster(DBClusterIdentifier=cluster_id)
            started.append(cluster_id)
            logger.info(f"Started Aurora cluster: {cluster_id}")
        except Exception as e:
            logger.error(f"Error starting Aurora cluster {cluster_id}: {e}")
    return started

def start_docdb_clusters(cluster_identifiers):
    """Start DocumentDB clusters"""
    started = []
    for cluster_id in cluster_identifiers:
        try:
            docdb.start_db_cluster(DBClusterIdentifier=cluster_id)
            started.append(cluster_id)
            logger.info(f"Started DocumentDB cluster: {cluster_id}")
        except Exception as e:
            logger.error(f"Error starting DocumentDB cluster {cluster_id}: {e}")
    return started

def start_ecs_services(services):
    """Scale ECS services back to original count"""
    started = []
    for svc in services:
        try:
            ecs.update_service(
                cluster=svc['cluster'],
                service=svc['service'],
                desiredCount=svc['desiredCount']
            )
            started.append(svc['service'])
            logger.info(f"Scaled ECS service to {svc['desiredCount']}: {svc['service']}")
        except Exception as e:
            logger.error(f"Error starting ECS service {svc['service']}: {e}")
    return started

def lambda_handler(event, context):
    """Main Lambda handler"""
    logger.info(f"Event: {json.dumps(event)}")

    tag_key = event.get('tag_key', 'Environment')
    tag_values = event.get('tag_values', ['dev', 'homolog', 'staging'])

    logger.info(f"Looking for stopped resources with tag {tag_key}={tag_values}")

    # Get stopped resources
    resources = get_stopped_resources(tag_key, tag_values)

    logger.info(f"Found stopped resources: {json.dumps(resources, default=str)}")

    # Start resources
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': 'start',
        'tag_key': tag_key,
        'tag_values': tag_values,
        'started': {
            'ec2': start_ec2_instances(resources['ec2']),
            'rds': start_rds_instances(resources['rds']),
            'aurora': start_aurora_clusters(resources['aurora']),
            'docdb': start_docdb_clusters(resources['docdb']),
            'ecs': start_ecs_services(resources['ecs'])
        }
    }

    logger.info(f"Results: {json.dumps(results)}")

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
