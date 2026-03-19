import random
import select, socket, sys
import time
# from util import *

SERVER = "irc.libera.chat"
PORT = 6667

DEFAULT_CHANNEL = "#TESTJMGDLS"
DEFAULT_NICKNAME = "JTC-Idiom-Bot"

# These can change for a better description
WHO_AM_I = f"{DEFAULT_NICKNAME} Jazzy De Los Santos, Timothy Matthies, Connor Villanueva CSC482-03"
USAGE_MSG_2 = "second line that explains what special abilities the bot has, including the special question (phase III) and an example of how to ask that question"


'''
Class defining the creation of an IRC connection and basic usages
'''
class IRC():
    def __init__(self, nickname: str = DEFAULT_NICKNAME):
        '''
        Initialize IRC socket

        [nickname] = DEFAULT_NICKANME = `JTC-bot####`
        '''
        self.nickname = nickname
        self.channels = []

        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def command(self, msg: str):
        '''
        Send a command to the IRC server

        EXAMPLE: "QUIT", "PING"
        '''

        if (len(self.channels) > 0):
            # print("Sending msg", msg)
            self.irc.send(bytes(msg + "\r\n", "UTF-8"))

    def send(self, msg: str, sender: str = "", channel: str = DEFAULT_CHANNEL, sleep_timer: float = 1.0,):
        '''
        Send a msg to a connected channel

        [channel] = DEFAULT_CHANNEL = `#csc482`

        [sleep_timer] -> How long to wait before responding
        '''
        time.sleep(sleep_timer)
        self.command("PRIVMSG " + channel + " :" + sender + ": " + msg)
        print("Sending: " + sender + ": " + msg)

    def connect(self, server = SERVER, port = PORT, channel : str = DEFAULT_CHANNEL):
        '''
        Connect to the IRC server and to a specific channel

        DEFAULT_CHANNEL = `#csc482`
        '''
        self.irc.connect((server, port))

        self.irc.send(f"NICK {self.nickname}\r\n".encode("UTF-8"))
        self.irc.send(f"USER {self.nickname} 0 * :Python IRC Bot\r\n".encode("UTF-8"))

        # Join the channel
        self.irc.send(f"JOIN {channel}\r\n".encode("UTF-8"))
        self.channels.append(channel)

    def get_response(self):
        '''
        Try to get a max of 2MB response from the server only if the msg is addressed to us

        Automatically reply "PONG" if the response is a ping.

        address_self -> Whether to wait for a messsage addressed to itself

        Timeout defined by random on interval [t_start, t_end]

        func -> Function used for parsing text
        '''

        res = self.irc.recv(2048).decode("UTF-8")

        if (res.find("PING") != -1):
            self.command("PONG " + res.split()[1] + "\r")

        return res

