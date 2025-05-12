# A dynamic DNS implementation via AWS

Based on https://github.com/awslabs/route53-dynamic-dns-with-lambda.

## Setup

 - `deploy_dyndns`: Deployment script for the entire system. Parameters at lines 5, 6 can be
configured as required.

 - `newrecord.py`: Configuration script for the AWS system. Used to specify 'possible' DNS records
and passphrases that authenticate clients that are authorized to create them.

 - `client/deploy_client`: Deployment script for clients that use the DDNS system.

### Details

 - `s3.cf.yml`: Creates an S3 bucket that can hold temporary Lambda code archives. Is created only
once and reused across all DDNS stacks.

 - `dyndns.cf.yml`: Creates all AWS resources for the dynamic DNS system. Can be used to create
multiple stacks for multiple domains/hosted zones.
