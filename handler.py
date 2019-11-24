import os
import json

import boto3
import requests

JEOPARDY_SHOWTIMES_API = 'https://api2.jeopardy.com/v2.1/tickets/showtimes'

def email_list(subject, message):
    recipients = [r.strip() for r in os.environ.get('EMAIL_LIST', '').split(',')]
    if recipients:
        client = boto3.client('ses')
        client.send_email(
            Source=os.environ['FROM_EMAIL'],
            Destination={
                'ToAddresses': recipients
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Text': {
                        'Data': message
                    }
                }
            })

def find_and_notify(event, context):
    try:
        r = requests.get(JEOPARDY_SHOWTIMES_API)
        r.raise_for_status()
        status_code = r.status_code
        result =r.json()
        showtimes = result['data']['showtimes']
        available_times = [t for t in showtimes if t['available']]
        total_showtimes = len(showtimes)
        body = {
            'message': 'Tickets available!' if available_times else 'No tickets available :(',
            'total': total_showtimes,
            'available': available_times,
        }
        subject = 'Jeopardy Ticket Bot Struck Out' if not available_times else 'Jeopardy Ticket Bot Found Tickets!!!'
        message = body['message']
        if available_times:
            message += '\n\n' + json.dumps(body['available'], sort_keys=True, indent=4)
        email_list(subject, message)
    except requests.HTTPError as e:
        status_code = e.response.status_code
        body = {
            'message': 'Failed to scrape showtimes',
            'response': e.response.content
        }
        email_list('Jeopardy Bot Failed to Scrape', json.dumps(body, indent=4))

    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }

    return response
