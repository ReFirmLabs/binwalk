# Provides scan status information via a TCP socket service.
# Currently only works for signature scans.

import time
import errno
import threading
import binwalk.core.compat

# Python 2/3 compatibility
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer


class StatusRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        message_format = "%s     %3d%%     [ %d / %d ]"
        last_status_message_len = 0
        status_message = ''
        message_sent = False

        self.server.binwalk.status.running = True

        while True:
            time.sleep(0.1)

            try:
                self.request.send(binwalk.core.compat.str2bytes('\b' * last_status_message_len))
                self.request.send(binwalk.core.compat.str2bytes(' ' * last_status_message_len))
                self.request.send(binwalk.core.compat.str2bytes('\b' * last_status_message_len))

                if self.server.binwalk.status.shutdown:
                    self.server.binwalk.status.finished = True
                    break

                if self.server.binwalk.status.total != 0:
                    percentage = ((float(self.server.binwalk.status.completed) / float(self.server.binwalk.status.total)) * 100)
                    status_message = message_format % (self.server.binwalk.status.fp.path,
                        percentage,
                        self.server.binwalk.status.completed,
                        self.server.binwalk.status.total)
                elif not message_sent:
                    status_message = "No status information available at this time!"
                else:
                    continue

                last_status_message_len = len(status_message)
                self.request.send(binwalk.core.compat.str2bytes(status_message))
                message_sent = True
            except IOError as e:
                if e.errno == errno.EPIPE:
                    break
            except Exception as e:
                binwalk.core.common.debug('StatusRequestHandler exception: ' + str(e) + '\n')
            except KeyboardInterrupt as e:
                raise e

        self.server.binwalk.status.running = False
        return


class ThreadedStatusServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


class StatusServer(object):

    def __init__(self, port, binwalk):
        self.server = ThreadedStatusServer(('127.0.0.1', port), StatusRequestHandler)
        self.server.binwalk = binwalk

        t = threading.Thread(target=self.server.serve_forever)
        t.setDaemon(True)
        t.start()
