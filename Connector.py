from abc import ABC, abstractmethod
from copy import deepcopy
import queue
import socket
import pickle
import codecs

import asyncio

import logging

interfaces = {} # dictionary to store interfaces -> {"IP:Port", "NetworkInterface"}


class NetworkInterface(ABC):


    @abstractmethod
    def connect(self, destinationIP, destinationPort):
        pass


    @abstractmethod
    def disconnect(self):
        pass


    @abstractmethod
    def send(self, message):
        pass


    @abstractmethod
    def receive(self, message):
        pass


    @abstractmethod
    def bind(self):

        pass

    @abstractmethod
    def getIP(self):
        pass


    @abstractmethod
    def getPort(self):
        pass


    @abstractmethod
    def getNumberOfMessages(self):
        pass


    @abstractmethod
    def getMessage(self):
        pass


class ServerProtocol(asyncio.DatagramProtocol):

    def __init__(self, queue):
        self.queue = queue


    def connection_made(self, transport):
        self.transport = transport


    def datagram_received(self, data, addr):
        #logging.info("ServerProtocol::datagram_received => Received datagram '%s' from %s" % (data, addr))
        message = pickle.loads(codecs.decode(data, "base64"))
        self.queue.put(message)


class RealNetworkInterface(NetworkInterface):


    def __init__(self, senderIP, senderPort):
        self.senderIP = senderIP
        self.senderPort = senderPort
        self.receiveQueue = queue.Queue()
        self.loop = asyncio.get_event_loop()


    def connect(self, destinationIP, destinationPort):

        self.destinationIP = destinationIP
        self.destinationPort = destinationPort
        #logging.info("RealNetwork::connect => Connecting to (%s:%d)" % (self.destinationIP, self.destinationPort))
        self.clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def disconnect(self):
        self.listen.close()


    def send(self, message):
        #logging.info("RealNetwork::send => Sending message '%s' to (%s:%d)" % (message.getPayload(), self.destinationIP, self.destinationPort))
        data = codecs.encode(pickle.dumps(message), "base64")
        self.clientSock.sendto(data, (self.destinationIP, self.destinationPort))


    def receive(self, message):
        self.receiveQueue.put(message)


    def bind(self):
        logging.info("RealNetworkInterface::bind => Registering (IP:Port) = (%s:%d )" % (self.senderIP, self.senderPort))
        self.listen = self.loop.create_datagram_endpoint(
            lambda: ServerProtocol(self.receiveQueue), local_addr=(self.senderIP, self.senderPort))
        self.loop.run_until_complete(self.listen)

        #self.transport, self.protocol
      #  try:
      #      self.loop.run_forever()
      #  except KeyboardInterrupt:
      #      pass

    def getIP(self):
        return self.senderIP


    def getPort(self):
        return self.senderPort


    def getNumberOfMessages(self):
        return self.receiveQueue.qsize()


    def getMessage(self):
        return self.receiveQueue.get()


class FakeNetworkInterface(NetworkInterface):


    def __init__(self, senderIP, senderPort):
        self.senderIP = senderIP
        self.senderPort = senderPort
        self.receiveQueue = queue.Queue()


    def connect(self, destinationIP, destinationPort):
        #logging.info("FakeNetwork::connect => Connecting (%s:%s) to (%s:%s)" % (self.senderIP, self.senderPort, destinationIP, destinationPort))
        self.destinationInterface = interfaces[destinationIP+":"+destinationPort]


    def disconnect(self):
        interfaces[self.senderIP + ":" + self.senderPort] = None


    def bind(self):
        logging.info("FakeNetworkInterface::bind => Registering (IP:Port) = (%s:%s )" % (self.senderIP, self.senderPort))
        interfaces[self.senderIP+":"+self.senderPort] = self


    def send(self, message):
        logging.debug("Sending message '%s' to destinationInterface (%s:%s)" % (message, self.destinationInterface.getIP(), self.destinationInterface.getPort()))
        self.destinationInterface.receive(deepcopy(message))


    def receive(self, message):
        logging.debug("Receive Queue of NIC (%s:%s) has <%d> messages" % (self.senderIP, self.senderPort, self.receiveQueue.qsize()))
        self.receiveQueue.put(message)
        logging.debug("Receive Queue of NIC (%s:%s) has <%d> messages" % (self.senderIP, self.senderPort, self.receiveQueue.qsize()))


    def getIP(self):
        return self.senderIP


    def getPort(self):
        return self.senderPort


    def getNumberOfMessages(self):
        return self.receiveQueue.qsize()


    def getMessage(self):
        return self.receiveQueue.get()
