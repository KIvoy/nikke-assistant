import sys
import trace
import threading
import time
from game_interaction_io import GameInteractionIO as gio
import keyboard


class ThreadWithTrace(threading.Thread):
    """
        A thread class that can be killed by calling .kill()
        original proposal here: https://web.archive.org/web/20130503082442/http://mail.python.org/pipermail/python-list/2004-May/281943.html
        do not use it for anything that could potentially deadlock you
        only use it for threads that you know well
    """

    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        threading.Thread.start(self)

    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


def thread_monitor(thread, key='delete', message_channel=None, logger=None):
    """
        a helper function to monitor a certain killable ThreadWithTrace
        waits for key to be pressed
        if pressed, kill the thread and release message to message_channel/logger wherever appropriate
    """
    while True:
        try:
            gio.delay(0.1)
            if keyboard.is_pressed(key):
                thread.kill()
                thread.join()
                if message_channel:
                    message_channel.set('DEL pressed')
                if logger:
                    logger.warning('DEL pressed to terminate task immediately')
            if not thread.is_alive():
                if logger:
                    logger.warning('Task terminated successfully')
                break
        except:
            break
    return True


def make_killable_thread(func, message_channel=None, logger=None):
    """
        a helper function to create a killable thread with no arguments
        it creates a killable thread with a monitor thread to terminate it early
    """
    t1 = ThreadWithTrace(target=func)
    t1.start()
    t2 = ThreadWithTrace(target=thread_monitor, args=(
        t1, 'delete', message_channel, logger))
    t2.start()
