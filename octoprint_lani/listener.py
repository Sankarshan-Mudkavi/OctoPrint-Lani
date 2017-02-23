# coding=utf-8
from __future__ import absolute_import

import json
import urllib2
import requests
import os
import yaml

from multiprocessing import Process

from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS

from octoprint.slicing.exceptions import SlicerNotConfigured

# Constants
MODULE_NAME = 'octoprint.plugins.lani.listener'

# Globals
messageHandler = None

class WebSocketProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        # print(response.peer)
        pass

    def onOpen(self):
        pass

    def onMessage(self, payload, isBinary):
        code, text = messageHandler(payload, isBinary)
        self.sendMessage(json.dumps({
            'code': code,
            'text': text,
        }).encode('utf-8'))

    def onClose(self, wasClean, code, reason):
        print('CLOSED---------')
        print('WebSocket connection closed: {0}'.format(reason))

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
    def __init__(self, logger, ws_url, data_folder):
        super(self.__class__, self).__init__()

        self.logger = logger

        global messageHandler
        messageHandler = self.__messageHandler

        self.ws_url = ws_url
        self.data_folder = data_folder

        with open(os.path.join(data_folder, '../../config.yaml'), 'r') as config_file:
            self.octoprint_api_key = yaml.load(config_file)['api']['key']

        self.octoprint_base_url = 'http://localhost:5000'

    # def __upload_file_to_octoprint(self, location)
    def __get_headers(self):
        return {
            'X-Api-Key': self.octoprint_api_key
        }

    def __messageHandler(self, payload, isBinary):
        if (isBinary):
            self.logger.info('Binary command received. Ignoring.')
            return

        try:
            self.logger.info('Command received: {}'.format(payload))
            message = json.loads(payload)

            if message['type'] == 'PRINT_STL':
                file_location = '{}/model.stl'.format(self.data_folder)

                self.logger.info('Downloading file.')
                res = urllib2.urlopen(message['url'])
                with open(file_location, 'w') as file:
                    file.write(res.read())

                self.logger.info('Uploading file.')
                url = '%s/api/files/local' % self.octoprint_base_url
                args = {
                    'headers': self.__get_headers(),
                    'files': {'file': open(file_location, 'rb')},
                    'params': {
                        'path': 'lani',
                    }
                }
                r = requests.post(url, **args)

                self.logger.info('Upload response: {}'.format(r.status_code))

                if r.status_code == 201:
                    self.logger.info('Slicing and printing.')
                    url = r.headers['location']
                    r = requests.post(url, headers=self.__get_headers(), json={
                        'command': 'slice',
                        'print': True,
                    })
                    self.logger.info('Slice command response: {}'.format(r.status_code))

                return r.status_code, r.text

            elif message['type'] == 'PRINT_GCODE':
                file_location = '{}/model.gcode'.format(self.data_folder)

                self.logger.info('Downloading file.')
                res = urllib2.urlopen(message['url'])
                with open(file_location, 'w') as file:
                    file.write(res.read())

                self.logger.info('Uploading file.')
                url = '%s/api/files/local' % self.octoprint_base_url
                args = {
                    'headers': self.__get_headers(),
                    'files': {'file': open(file_location, 'rb')},
                    'params': {
                        'path': 'lani',
                        'print': 'true',
                    }
                }
                r = requests.post(url, **args)

                self.logger.info('Upload response: {}'.format(r.status_code))

                return r.status_code, r.text

            elif message['type'] == 'STOP':
                url = '%s/api/job' % self.octoprint_base_url
                r = requests.post(url, headers=self.__get_headers(), json={
                    'command': 'cancel'
                })
                return r.status_code, r.text
        except KeyError as e:
            self.logger.info('KeyError')
            return 500, 'Internal error: ' + e
        except ValueError as e:
            self.logger.info('ValueError')
            return 500, 'Internal error: ' + e
        except IOError as e:
            self.logger.info('ValueError')
            return 500, 'Internal error: ' + e
        except SlicerNotConfigured as e:
            self.logger.info('Error: slicer is not configured')
            return 400, 'Slicer not configured'

    def run(self):
        self.logger.info('Listener started.')
        twistedLogger = log.PythonLoggingObserver(loggerName=MODULE_NAME + '.twisted')
        twistedLogger.start()

        factory = WebSocketFactory(self.ws_url)
        factory.protocol = WebSocketProtocol

        connectWS(factory)
        reactor.run()
