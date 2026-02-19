from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json
from processData import process

notification_receiver = None

class NotificationReceiver(BaseHTTPRequestHandler):
    """ The notification handler class. 
        This class handles the HTTP requests sent by the CSE to the notification receiver.
    """
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request_id = self.headers['X-M2M-RI']
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        if data['m2m:sgn'].get('vrq'):
            print('<= Verification notification request received')
        else:
            print('<= Subscription notification request received')
        print(f'<= {data}')

        process(data)

        self.send_response(200)
        self.send_header('X-M2M-RSC', '2000')
        self.send_header('X-M2M-RI', request_id)

        self.end_headers() 


    def log_message(self, format:str, *args:int) -> None:
        # Ignore log messages
        pass






def run_notification_receiver(port=9000) -> None:
    """ This function starts the notification receiver on the specified port.
        The notification receiver will run in a separate thread.

        Args:
            handler_class: The HTTP request handler class
            port: The port on which the notification server will run
    """
    global notification_receiver
    server_address = ('', port)
    # HTTPServer(("0.0.0.0", 9000), H).serve_forever()
    notification_receiver = HTTPServer(server_address, NotificationReceiver)
    print(f'Starting notification receiver on port {port}')
    Thread(target=notification_receiver.serve_forever).start()


def stop_notification_receiver() -> None:
    """ Stop the notification receiver.
    """
    global notification_receiver
    if notification_receiver:
        notification_receiver.shutdown()
        notification_receiver = None
        print('Notification receiver stopped')