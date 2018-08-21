#! /usr/local/bin/python3
from client import ChatClient
import threading
import socket
import sys


PORT = 9876


class ChatServer(threading.Thread):
    def __init__(self, port, host='localhost'):
        super().__init__(daemon=True)
        self.port = port
        self.host = host
        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP
        )
        self.client_pool = []

        try:
            self.server.bind((self.host, self.port))
        except socket.error:
            print('Bind failed {}'.format(socket.error))
            sys.exit()

        self.server.listen(10)

    def parser(self, id, nick, conn, message):
        if message.decode().startswith('@'):
            data = message.decode().split(maxsplit=1)

            if data[0] == '@quit':
                conn.sendall(b'You have left the chat.')
                reply = nick.encode() + b'has left the channel.\n'
                [c.conn.sendall(reply) for c in self.client_pool if len(self.client_pool)]
                self.client_pool = [c for c in self.client_pool if c.id != id]
                conn.close()

            if data[0] == '@list':
                reply = ''
                for c in self.client_pool:
                    reply += c.nick + ' \n'
                [c.conn.sendall(reply.encode()) for c in self.client_pool if len(self.client_pool)]
                return('')

            if data[0] == '@nickname':
                for i in self.client_pool:
                    if i.id == id:
                        i.update_nickname(data[1])
                        reply = 'Username updated to ' + data[1] + ' \n'
                        [c.conn.sendall(reply.encode()) for c in self.client_pool if len(self.client_pool)]
                        return(i.nick)

            elif data[0] == '@dm':
                for i in self.client_pool:
                    data = message.decode().split(maxsplit=2)
                    if i.nick.rstrip() == data[1]:
                        i.conn.sendall(data[2].encode())

            else:
                conn.sendall(b'Invalid command. Please try again.\n')
                return('')

        else:
            reply = nick.encode() + b': ' + message
            [c.conn.sendall(reply) for c in self.client_pool if len(self.client_pool)]
            return('')

    def run_thread(self, id, nick, conn, addr):
        print('{} connected with {}:{}'.format(nick, addr[0], str(addr[1])))
        try:
            while True:
                data = conn.recv(4096)
                parsed_nickname = self.parser(id, nick, conn, data)
                if len(parsed_nickname):
                    nick = parsed_nickname
        except (ConnectionResetError, BrokenPipeError, OSError):
            conn.close()

    def run(self):
        print('Server running on {}'.format(PORT))
        while True:
            conn, addr = self.server.accept()
            client = ChatClient(conn, addr)
            self.client_pool.append(client)
            threading.Thread(
                target=self.run_thread,
                args=(client.id, client.nick, client.conn, client.addr),
                daemon=True
            ).start()

    def exit(self):
        self.server.close()


if __name__ == '__main__':
    server = ChatServer(PORT)
    try:
        server.run()
    except KeyboardInterrupt:
        [c.conn.close() for c in server.client_pool if len(server.client_pool)]
        server.exit()
