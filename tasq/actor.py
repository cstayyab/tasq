# -*- coding: utf-8 -*-

"""
tasq.actor.py
~~~~~~~~~~~~~
"""

from queue import Queue
from threading import Thread, Event


class ActorExit(Exception):
    pass


class Actor:

    """Class modeling a basic erlang-style actor, a simple object which can be used to push messages
    into a mailbox and process them in separate thread, concurrently, without sharing any state with
    other actors"""

    def __init__(self):
        self._mailbox = Queue()
        self._terminated = Event()

    def send(self, msg):
        """Sends a message to the actor, effectively putting it into the mailbox"""
        self._mailbox.put(msg)

    def recv(self):
        """Poll the mailbox for pending messages, blocking if empty. In case of `ActorExit` message
        it raises an execption and shutdown the actor loop"""
        msg = self._mailbox.get()
        if msg is ActorExit:
            raise ActorExit()
        return msg

    def close(self):
        """Shutdown the actor by sending an `ActorExit` to the mailbox"""
        self.send(ActorExit)

    def start(self):
        """Run the processing thread"""
        t = Thread(target=self._bootstrap, daemon=True)
        t.start()

    def _bootstrap(self):
        """Target method to be run into a thread, call the `run` method till an `ActorExit`
        message"""
        try:
            self.run()
        except ActorExit:
            pass
        finally:
            self._terminated.set()

    def join(self):
        """Wait till the end of all messages"""
        self._terminated.wait()

    def run(self):
        """Must be implemented by subclasses"""
        pass


class Result:

    """Simple class to wrap a result for processed jobs"""

    def __init__(self):
        self._event = Event()
        self._result = None

    def set_result(self, value):
        self._result = value
        self._event.set()

    def result(self, timeout=None):
        self._event.wait(timeout)
        return self._result
