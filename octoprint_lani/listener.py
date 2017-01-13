# coding=utf-8
from __future__ import absolute_import

import logging
import json

from multiprocessing import Process

from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS


# Constants
MODULE_NAME = 'octoprint.plugins.lani.listener'

# Globals
uuid = ''

logger = logging.getLogger(MODULE_NAME)
# TODO: use this ^


class WebSocketProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        print('CONNECT')
        print(response.peer)

    def onOpen(self):
        global uuid
        print(uuid)
        print('OPEN')
        self.sendMessage(json.dumps({
            'uuid': uuid
        }).encode('utf-8'))

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

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
    def __init__(self, id, oskr_url):
        super(self.__class__, self).__init__()
        global uuid
        uuid = id
        self.oskr_url = oskr_url

    def run(self):
        print(self.oskr_url)
        logger.info('Listener thread created.')
        twistedLogger = log.PythonLoggingObserver(loggerName=MODULE_NAME + '.twisted')
        twistedLogger.start()

        factory = WebSocketFactory(self.oskr_url)
        factory.protocol = WebSocketProtocol

        connectWS(factory)
        reactor.run()
