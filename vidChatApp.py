import logging
import threading
import time
import uuid
import json
import tornado.web
import tornado.websocket
logger = logging.getLogger(__name__)


# ===============================================================================
# HomePage- Default homepage for hello
# ===============================================================================
class HomePage(tornado.web.RequestHandler):
    def get(self):
        self.render("sources/index.html")


# ===============================================================================
# PageStream- Testing page to stream audio and video
# ===============================================================================
class PageStream(tornado.web.RequestHandler):
    def get(self):
        self.render("sources/viewMe.html")


# ===============================================================================
# ChatRoomSocket- Stream Web cam and connect
# ===============================================================================
class ChatRoomSocket(tornado.websocket.WebSocketHandler):
    _ROOMCONNECTIONS = {}

    def open(self):
        self._name = None
        self._id = None
        logger.info(self._ROOMCONNECTIONS)

    def on_message(self, message):
        data = json.loads(message)
        if data.get('joinChat'):
            if data.get('joinChat') in self._ROOMCONNECTIONS:
                self._ROOMCONNECTIONS[data.get('joinChat')].append(self)
            else:
                self._ROOMCONNECTIONS[data.get('joinChat')] = [self]
            if not self._name:
                self._name = data.get('personName')
            if not self._id:
                self._id = uuid.uuid4().hex[:8]
            logger.info("{} Joined the {} chatroom".format(self._name,
                                                           data.get('joinChat')))
            count = len(self._ROOMCONNECTIONS[data.get('joinChat')])
            people = [
                c._name for c in self._ROOMCONNECTIONS[data.get('joinChat')]]
            # peers = [
            #     c._id for c in self._ROOMCONNECTIONS[data.get('joinChat')]]
            for connection in self._ROOMCONNECTIONS[data.get('joinChat')]:
                connection.write_message({'count': count,
                                          'people': people,
                                          'lastPeer': self._id,
                                          'id': connection._id,
                                          'messageType': 'init'})
        else:
            if data.get('chatID'):
                if data.get("messageType") == "text":
                    logger.info("{} messaged the {} chatroom".format(self._name,
                                                                     data.get('chatID')))
                    count = len(self._ROOMCONNECTIONS[data.get('chatID')])
                    for connection in self._ROOMCONNECTIONS[data.get('chatID')]:
                        connection.write_message({'count': count,
                                                  'messagePersonName': self._name,
                                                  'messageType':
                                                  data.get("messageType"),
                                                  'message':
                                                  data.get('message')
                                                  })
                if data.get("messageType") == "offer":
                    for connection in self._ROOMCONNECTIONS[data.get('chatID')]:
                        if connection._id == data.get("peerId"):
                            logger.info("{} offer to {}".format(
                                self._name, connection._name))
                            connection.write_message({'messageType': "offer",
                                                      'offer': data.get('offer'),
                                                      'peerId': self._id})
                if data.get("messageType") == "response":
                    for connection in self._ROOMCONNECTIONS[data.get('chatID')]:
                        if connection._id == data.get("peerId"):
                            logger.info("{} response to {}".format(
                                self._name, connection._name))
                            connection.write_message({'messageType': "response",
                                                      'answer': data.get('answer'),
                                                      'peerId': self._id})
                if data.get("messageType") == "negotiate":
                    for connection in self._ROOMCONNECTIONS[data.get('chatID')]:
                        if connection._id == data.get("peerId"):
                            logger.info("{} negotiate with {}".format(
                                self._name, connection._name))
                            if data.get("offer"):
                                connection.write_message({'messageType': "negotiate",
                                                          'offer': data.get('offer'),
                                                          'peerId': self._id})
                            if data.get("answer"):
                                connection.write_message({'messageType': "negotiate",
                                                          'answer': data.get('answer'),
                                                          'peerId': self._id})
                if data.get("messageType") == "ice":
                    for connection in self._ROOMCONNECTIONS[data.get('chatID')]:
                        if connection._id == data.get("peerId"):
                            logger.info("{} ice with {}".format(
                                self._name, connection._name))
                            connection.write_message({'messageType': "ice",
                                                      'ice': data.get('ice'),
                                                      'peerId': self._id})

    def on_close(self):
        for chatID, connectionBlock in self._ROOMCONNECTIONS.items():
            if self in connectionBlock:
                self._ROOMCONNECTIONS[chatID].remove(self)
                logger.info("{} left {}".format(
                    self._name, chatID))
                count = len(self._ROOMCONNECTIONS[chatID])
                people = [c._name for c in self._ROOMCONNECTIONS[chatID]]
                for connection in self._ROOMCONNECTIONS[chatID]:
                    connection.write_message({'count': count,
                                              'people': people,
                                              'messageType': 'init'})
                    connection.write_message({'peerId': self._id,
                                              'messageType': 'remove',
                                              'count': count})


# ===============================================================================
# Chat- Main page to connect chat rooms
# ===============================================================================
class Chat(tornado.web.RequestHandler):
    def get(self):
        self.render("sources/chatRoom2.html")
