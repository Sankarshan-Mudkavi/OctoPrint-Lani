# coding=utf-8
from __future__ import absolute_import

import logging
import json
import urllib2
import requests

from multiprocessing import Process

from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS


# Constants
MODULE_NAME = 'octoprint.plugins.lani.listener'

# Globals
messageHandler = None

logger = logging.getLogger(MODULE_NAME)
# TODO: use this ^


class WebSocketProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        print('CONNECT')
        print(response.peer)

    def onOpen(self):
        # global uuid
        # print(uuid)
        print('OPEN')
        # self.sendMessage(json.dumps({
        #     'uuid': uuid
        # }).encode('utf-8'))

    def onMessage(self, payload, isBinary):
        code, text = messageHandler(payload)
        self.sendMessage(json.dumps({
            'code': code,
            'text': text,
        }).encode('utf-8'))
        # TODO: send back message id,
        # if isBinary:
        #     print("Binary message received: {0} bytes".format(len(payload)))
        # else:
        #     print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print('CLOSED---------')
        print("WebSocket connection closed: {0}".format(reason))

    def onError(self):
        print('ERROR')


class WebSocketFactory(ReconnectingClientFactory, WebSocketClientFactory):
    protocol = WebSocketProtocol

    # http://twistedmatrix.com/documents/current/api/twisted.internet.protocol.ReconnectingClientFactory.html
    initialDelay = 5
    maxDelay = 5
    jitter = 0

    def startedConnecting(self, connector):
        print('Connecting to oskr at {}'.format(self.url))

    def clientConnectionLost(self, connector, reason):
        print('Lost connection. Reason: {}'.format(reason))
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason: {}'.format(reason))
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


class LaniListener(Process):
    def __init__(self, id, oskr_url, data_folder):
        super(self.__class__, self).__init__()
        global messageHandler
        messageHandler = self.__messageHandler
        self.oskr_url = oskr_url + '?uuid=' + id
        self.data_folder = data_folder
        self.octoprint_api_key = '3379659B413148449175F11FD806B68C'
        self.octoprint_base_url = 'http://localhost:5000'

    # def __upload_file_to_octoprint(self, location)
    def __get_headers(self):
        return {
            'X-Api-Key': self.octoprint_api_key
        }

    def __messageHandler(self, payload):
        try:
            message = json.loads(payload)
            print(message)

            if message["type"] == "PRINT_STL":
                model_file_location = "{}/model.stl".format(self.data_folder)

                print('Downloading file')
                res = urllib2.urlopen(message["url"])
                with open(model_file_location, 'w') as file:
                    file.write(res.read())

                print('Uploading file')
                url = '%s/api/files/local' % self.octoprint_base_url
                args = {
                    'headers': self.__get_headers(),
                    'files': {'file': open(model_file_location, 'rb')},
                    'params': {
                        'path': 'lani',
                    }
                }
                r = requests.post(url, **args)
                print('---------------------------')
                print(r.url)
                print(r.status_code)
                print(r.headers['location'])
                print(r.text)

                if r.status_code == 201:
                    print('Printing')
                    url = r.headers['location']
                    r = requests.post(url, headers={
                        'X-Api-Key': self.octoprint_api_key,
                    }, json={
                        'command': 'slice',
                        'print': True,
                    })
                    print(r.status_code)
                    print(r.text)

                return r.status_code, r.text

            elif message["type"] == "STOP":
                self._printer.stop()
            print('handled')
        # except (KeyError, ValueError, IOError, octoprint.slicing.exceptions.SlicerNotConfigured):
        except (KeyError):
            print("Invalid message")
            return 500, "Internal error"

    def run(self):
        print(self.oskr_url)
        logger.info('Listener thread created.')
        twistedLogger = log.PythonLoggingObserver(loggerName=MODULE_NAME + '.twisted')
        twistedLogger.start()

        factory = WebSocketFactory(self.oskr_url)
        factory.protocol = WebSocketProtocol

        connectWS(factory)
        reactor.run()
