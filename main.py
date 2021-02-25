import json
import program
import uuid
import string
import random
import logging


def random_string():
    return ''.join(random.choice(string.ascii_letters) for i in range(10))


logging.basicConfig(level=logging.INFO)

body = {
    'name': f'{random_string()} {random_string()}',
    'email-address': f'{random_string()}@{random_string()}.com',
    'first-preference': f'{random_string()}'
}

test_event_body = json.dumps(body)
test_event = {'body': test_event_body}
test_context = type('obj', (object,), {'aws_request_id': str(uuid.uuid4())})()
print(program.lambda_handler(test_event, test_context))
