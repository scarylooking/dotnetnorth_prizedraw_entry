import json
import boto3
import uuid
import logging
import os


def lambda_handler(event, context):
    bucket_name = os.environ.get('bucket_name', None)

    if not environment_configured(bucket_name):
        return {'statusCode': 500}

    body = json.loads(event.get('body', '{}'))

    name = body.get('name', None)
    email = body.get('email-address', None)
    prize = body.get('first-preference', None)

    if name is None or not name:
        logging.error(f'Rejecting request because name parameter is missing or invalid: {name}')
        return {'statusCode': 400}

    if email is None or not email:
        logging.error(f'Rejecting request because email parameter is missing or invalid: {email}')
        return {'statusCode': 400}

    if prize is None or not prize:
        logging.error(f'Rejecting request because prize parameter is missing or invalid: {prize}')
        return {'statusCode': 400}

    ticket_id = str(uuid.uuid4())

    if not write_entry(bucket_name, ticket_id, name, email, prize):
        return {'statusCode': 400}

    logging.info(f'successfully recorded entry {ticket_id} from {name}')

    return {
        'statusCode': 200,
        'body': {
            'id': ticket_id
        },
        'headers': {
            'Content-Type': 'application/json',
            'x-powered-by': 'al.paca'
        }
    }


def write_entry(bucket_name:str, ticket_id: str, name: str, email: str, prize: str):
    payload = {
        'ticket': ticket_id,
        'name': name,
        'email': email,
        'prize': prize,
    }

    entry_file_name = f'entry/{ticket_id}.json'
    logging.info(f'writing entry information to s3://{bucket_name}/{entry_file_name}')

    try:
        s3 = get_s3_client()
        s3.put_object(Body=(bytes(json.dumps(payload).encode('UTF-8'))), Bucket=bucket_name, Key=entry_file_name)
    except Exception as e:
        logging.error(f'failed to write entry {ticket_id} due to an exception: {str(e)}')
        return False

    return True


def get_s3_client():
    return boto3.client('s3')


def environment_configured(bucket_name: str):
    if bucket_name is None or not bucket_name:
        logging.error(f'bucket_name is not set')
        return False

    aws_key = os.environ.get('aws_access_key_id', None)
    if aws_key is None or not aws_key:
        logging.error(f'aws_key is not set')
        return False

    aws_secret = os.environ.get('aws_secret_access_key', None)

    if aws_secret is None or not aws_secret:
        logging.error(f'aws_secret is not set')
        return False

    return True
