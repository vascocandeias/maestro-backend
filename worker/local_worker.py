import common
import pika
import json
import threading
import functools
import sys
import os
from socket import gaierror

def ack_message(channel, tag):
    if channel.is_open:
        channel.basic_ack(tag)
    else:
        # Channel is already closed
        print("Ack error")


def run(channel, tag, body, connection):
    common.exec(body)

    cb = functools.partial(ack_message, channel, tag)
    connection.add_callback_threadsafe(cb)


def callback(channel, method, properties, body, connection):
    body = json.loads(body)
    print("Message: " % body)
    try:
        t = threading.Thread(target=run, args=(channel, method.delivery_tag, body, connection))
        t.start()
    except Exception as e:
        print("ERROR: ", e)
        print("Unable to start thread")


def main():
    credentials = pika.PlainCredentials('worker', 'worker')

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', credentials=credentials))
    except gaierror:
        connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1', credentials=credentials))
        print("Using 127.0.0.1 server")

    channel = connection.channel()

    cb = functools.partial(callback, connection=connection)
    channel.basic_consume(queue='requests',
                        on_message_callback=cb)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        if channel.is_open:
            channel.stop_consuming()
        raise

if __name__ == '__main__':
    while True:
        try:
            main()
        except pika.exceptions.ConnectionClosedByBroker:
            print("Connection closed")
            continue
        except pika.exceptions.AMQPConnectionError:
            continue
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)