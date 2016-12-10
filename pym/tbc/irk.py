from __future__ import unicode_literals

import json
import socket
import sys

DEFAULT_SERVER = ("192.168.0.5", 6659)

def connect(server = DEFAULT_SERVER):
	return socket.create_connection(server)

def send(s, target, message):
	data = {"to": target, "privmsg" : message}
	s.sendall(json.dumps(data).encode('ascii'))

def irk(target, message, server = DEFAULT_SERVER):
	s = connect(server)
	if "irc:" not in target and "ircs:" not in target:
		target = "irc://chat.freenode.net/{0}".format(target)
		send(s, target, message)
	s.close()

def send_irk(msg, host):
	target = "tinderbox-cluster"
	try:
		irk(target, msg, server = (host, 6659)
	except socket.error as e:
		sys.stderr.write("irk: write to server failed: %r\n" % e)
