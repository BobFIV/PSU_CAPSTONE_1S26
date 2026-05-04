from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import json

notification_receiver = None
TARGET_AE_NAME = "gatewayAgent"

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

            try:
                rep = data['m2m:sgn']['nev']['rep']

                if 'm2m:ae' not in rep:
                    print("Ignoring: NOT AE creation")
                else:
                    ae = rep['m2m:ae']

                    ae_name = ae.get('rn')

                    print(f"AE detected: {ae_name}")

                    if ae_name != TARGET_AE_NAME:
                        print(f"Ignored AE: {ae_name}")
                    else:
                        print("gatewayAgent AE detected")
                        #add some hadler function for later
                        try:
                            from . import services
                            record = services.handle_gateway_agent_notification(ae)
                            print(f"Topology updated from notification: {record}")
                        except Exception as e:
                            print(f"Error updating topology from notification: {e}")
            except Exception as e:
                print(f"Error processing notification: {e}")

        self.send_response(200)
        self.send_header('X-M2M-RSC', '2000')
        self.send_header('X-M2M-RI', request_id)

        self.end_headers() 


    def log_message(self, format:str, *args:int) -> None:
        # Ignore log messages
        pass

def run_notification_receiver(port=7070) -> None:
    """ This function starts the notification receiver on the specified port.
        The notification receiver will run in a separate thread.

        Args:
            handler_class: The HTTP request handler class
            port: The port on which the notification server will run
    """
    global notification_receiver
    server_address = ('', port)
    HTTPServer.allow_reuse_address = True
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