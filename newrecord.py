#!/usr/bin/env python
'''
Inspired by https://github.com/awslabs/route53-dynamic-dns-with-lambda.

I didn't like their code and user interface at all, so I rewrote it. This
version is almost entirely new, but just to be clear: The original file by which
this code was inspired is licensed under Apache 2.0. See LICENSE-THIRD-PARTY.txt
for details.
'''

import argparse
import json

import boto3

def find_physical_id(stack_name: str, logical_id: str) -> None | object:
    cloudformation = boto3.client('cloudformation')
    resources = cloudformation.list_stack_resources(StackName=stack_name)
    for resource in resources['StackResourceSummaries']:
        if resource['LogicalResourceId'] == logical_id:
            return resource['PhysicalResourceId']
    return None

def main(args):
    stack_name = args.stack_name

    dynamodb = boto3.client('dynamodb')
    route53 = boto3.client('route53')

    # Check that the cloudformation stack exists
    try:
        cloudformation = boto3.client('cloudformation')
        cloudformation.describe_stacks(StackName=stack_name)
    except:
        print(f'Stack {stack_name} not found. This can happen when the current'
              ' AWS CLI profile doesn\'t have the appropriate permissions. Are'
              ' you using the right profile?')
        exit(1)

    # Get dynamodb table name and Lambda Function URL
    table = find_physical_id(stack_name, args.table_logical_id)
    if table is None:
        print(f'DynamoDB table with logical ID {args.table_logical_id} not found.')
        exit(1)

    hostname = args.hostname
    if hostname is None:
        hostname = input('Hostname: ')
    hostedzone = args.hostedzone
    if hostedzone is None:
        hostedzone = input('HostedZone: ')

    # Resolve hosted zone name to hosted zone ID
    try:
        hz = route53.list_hosted_zones_by_name(MaxItems='1', DNSName=hostedzone)
        hz = hz['HostedZones'][0]
        assert(hz['Name'] == hostedzone or hz['Name'] == hostedzone+'.')
        hostedzone = hz['Id'].split('/')[2]
    except:
        print(f'Hosted zone {hostedzone} not found.')
        exit(1)

    ttl = args.ttl
    if ttl is None:
        ttl = int(input('TTL: '))
    else:
        ttl = int(args.ttl)
    secret = args.secret
    if secret is None:
        secret = input('Secret: ')
    data_obj = {
        'route_53_zone_id': hostedzone,
        'route_53_record_ttl': ttl,
        'shared_secret': secret
    }

    dynamodb.put_item(
        TableName = table,
        Item = {
            'hostname': {
                'S': hostname,
            },
            'data': {
                'S': json.dumps(data_obj),
            },
        }
    )

    # Verify
    resp = dynamodb.get_item(
        TableName=table,
        Key={'hostname': {'S': hostname}}
    )
    data = json.loads(resp["Item"]["data"]["S"])
    data["shared_secret"] = "*" * len(data["shared_secret"])
    print(f'New table item: {data}')

if __name__ == "__main__":
    desc = '''Adds an allowed DDNS record to the Lambda's internal database.

Any required variables not specified as options (--hostname, --hostedzone,
--ttl, --secret) will be queried interactively via STDIN.
'''

    program = argparse.ArgumentParser()
    program.description = desc
    program.add_argument(
        'stack_name',
        help='Name of a DDNS CloudFormation stack. The new record will be'
             ' created in this stack\'s DynamoDB table.'
    )
    program.add_argument('--hostname')
    program.add_argument('--hostedzone')
    program.add_argument('--ttl', type=int)
    program.add_argument('--secret',
                         help='Secret (a password) shared between the DDNS'
                              ' client and AWS.')
    program.add_argument(
        '--table-logical-id',
        help='The logical ID of the DNS records table in the specified stack.'
             ' This is only required when a non-default parameter was used'
             ' to create the resource/stack.',
        default='DynDNSHostnameTable'
    )
    args = program.parse_args()

    main(args)
