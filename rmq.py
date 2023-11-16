#!/usr/bin/env python

import json

import pika


def start_rabbitmq_processor(
        requests_q: str,
        rabbit_host: str,
        rabbit_username: str,
        rabbit_password: str,
        rabbit_vhost: str,
        process_job_requests_fn,
):
    if rabbit_vhost is not None:
        rabbit_vhost = rabbit_vhost.strip()
        if rabbit_vhost == "/" or rabbit_vhost == "":
            rabbit_vhost = None

    if rabbit_vhost is None:
        params = pika.ConnectionParameters(
            host=rabbit_host,
            credentials=pika.PlainCredentials(rabbit_username, rabbit_password),
            heartbeat=0
        )
    else:
        params = pika.ConnectionParameters(
            host=rabbit_host,
            virtual_host=rabbit_vhost,
            credentials=pika.PlainCredentials(rabbit_username, rabbit_password),
            heartbeat=0
        )

    with pika.BlockingConnection(params) as connection:
        with connection.channel() as channel:
            for method_frame, properties, json_request in channel.consume(requests_q):
                try:
                    replies_q = properties.reply_to
                    result = process_job_requests_fn(properties, json.loads(json_request))
                    json_response: str = json.dumps(result)
                    basic_properties = pika.BasicProperties(
                        correlation_id=properties.correlation_id,
                        content_type="text/plain",
                        delivery_mode=1,
                    )
                    channel.basic_publish(
                        '',
                        replies_q,
                        json_response,
                        basic_properties
                    )
                    channel.basic_ack(method_frame.delivery_tag)

                except BaseException as ex:
                    print(f"something went terribly awry in processing the message. it's all crap! {ex}")
