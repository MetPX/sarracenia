#!/usr/bin/env python3
"""

  Trivial http server in python, only for testing, not deployment.
  serves current working directory on PORT

"""

import http.server
import socketserver

PORT = 8001

Handler = http.server.SimpleHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)

print("serving at port", PORT)
httpd.serve_forever()
