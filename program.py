import json
import boto3
import uuid
import logging
import os
import utility
import hashlib
import html

utility.configure_logger()


def lambda_handler(event, context):
    bucket_name = os.environ.get('bucket_name', None)

    if not environment_configured(bucket_name):
        return {'statusCode': 500}

    body = json.loads(event.get('body', None))

    if body is None or not body:
        logging.error(f'Rejecting request because body is missing or invalid')
        return {'statusCode': 400}

    name = safe_get_string(body, 'name')

    if name is None or not name:
        logging.error(f'Rejecting request because name parameter is missing or invalid: {name}')
        return {'statusCode': 400}

    email = safe_get_string(body, 'email-address')

    if email is None or not email:
        logging.error(f'Rejecting request because email parameter is missing or invalid: {email}')
        return {'statusCode': 400}

    prize = safe_get_string(body, 'first-preference')

    if prize is None or not prize:
        logging.error(f'Rejecting request because prize parameter is missing or invalid: {prize}')
        return {'statusCode': 400}

    ticket_id = str(uuid.uuid4())
    identity = generate_identity(event)

    if not write_entry(bucket_name, ticket_id, name, email, prize, identity):
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


def safe_get_string(body, property_name: str, min_len: int = 1, max_len: int = 255):
    value = body.get(property_name, None)

    if value is None or not value:
        return None

    if len(value) > max_len:
        return None

    escaped_string = html.escape(value)

    ascii_encoded_string = escaped_string.encode(encoding='ascii', errors='ignore').decode()

    stripped_string = " ".join(ascii_encoded_string.split()).strip()

    if stripped_string is None or not stripped_string:
        return None

    if len(stripped_string) < min_len:
        return None

    return stripped_string


def write_entry(bucket_name: str, ticket_id: str, name: str, email: str, prize: str, identity: str):
    payload = {
        'ticket': ticket_id,
        'name': name,
        'email': email,
        'prize': prize,
        'identity': identity
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


def generate_identity(event):
    headers = json.loads(event.get('headers', None))

    if headers is None:
        return ''

    ip = headers.get('X-Forwarded-For', None)
    agent = headers.get('User-Agent', None)

    if ip is None and agent is None:
        return ''

    return hashlib.sha512(f'{ip}-{agent}'.encode('utf-8')).hexdigest()


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
