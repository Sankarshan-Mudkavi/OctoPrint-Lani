# coding=utf-8
from __future__ import absolute_import

import logging

from multiprocessing import Process

from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory, connectWS


# Constants
# TODO: don't hardcode this
# OSKR_WEBSOCKET_URL = 'ws://127.0.0.1:5443'
OSKR_WEBSOCKET_URL = 'ws://52.229.122.32:5443'
MODULE_NAME = 'octoprint.plugins.lani.listener'

logger = logging.getLogger(MODULE_NAME)


class WebSocketProtocol(WebSocketClientProtocol):
    def onConnect(self, response):
        print('CONNECT')
        print(response.peer)

    def onOpen(self):
        print('OPEN')

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
        print('Connecting to {}'.format(OSKR_WEBSOCKET_URL))

    def clientConnectionLost(self, connector, reason):
        print('Lost connection. Reason: {}'.format(reason))
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason: {}'.format(reason))
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


class LaniListener(Process):
    def run(self):
        logger.info('Listener thread created.')
        twistedLogger = log.PythonLoggingObserver(loggerName=MODULE_NAME + '.twisted')
        twistedLogger.start()

        factory = WebSocketFactory(OSKR_WEBSOCKET_URL)
        factory.protocol = WebSocketProtocol

        connectWS(factory)
        reactor.run()
