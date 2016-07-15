import json
import socket
from collections import OrderedDict

import h2.connection
import h2.events

def send_response(conn, event):
    """
    Set response headers and body and responds.
    """
    # stream ids are unique and progressive per connection
    # every event is bound to a stream
    stream_id = event.stream_id
    response_data = dict(event.headers)
    response_data['text'] = 'it works!'
    response_data = json.dumps(response_data).encode('utf-8')

    conn.send_headers(
        stream_id=stream_id,
        headers=OrderedDict([
            (':status', '200'),
            ('server', 'basic-h2-server/1.0'),
            ('content-length', str(len(response_data))),
            ('content-type', 'application/json'),
        ])
    )
    conn.send_data(
        stream_id=stream_id,
        data=response_data,
        end_stream=True
    )

def handle(sock):
    """
    Server main loop.
    """
    conn = h2.connection.H2Connection(client_side=False)
    
    # HTTP/2 preamble
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())  # H2Connection.data_send manages internal h2 buffer

    while True:
        data = sock.recv(65535)
        if not data:
            break
        
        # retrieve events from the interface
        events = conn.receive_data(data)
        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                send_response(conn, event)

        # send the content of the buffer
        data_to_send = conn.data_to_send()
        if data_to_send:
            sock.sendall(data_to_send)


sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 8080))
sock.listen(5)

while True:
    handle(sock.accept()[0])
