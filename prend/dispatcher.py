import copy
import datetime
import logging
import requests
import schedule
import threading
from queue import Queue, Empty
from prend.channel import Channel, OhIllegalChannelException
from prend.action import Action, OhIllegalActionException


_logger = logging.getLogger(__name__)


class DispatcherException(Exception):
    pass


class ActionListener:
    def __init__(self):
        self.channel: Channel = None
        self.listener = None
        self.type = None


class DispatcherActionSink:
    def push_action(self, root_action: Action) -> None:
        """overwrite for testing"""
        pass


class Dispatcher(DispatcherActionSink):

    def __init__(self):
        self._lock_channel_listeners = threading.Lock()
        self._channel_listeners = {}
        self._action_queue = Queue()  # synchronized
        self._last_cron_run = datetime.datetime.now() - datetime.timedelta(days=1)

    def register_oh_listener(self, channel: Channel, listeners) -> None:

        if not channel or not channel.is_valid():
            raise OhIllegalChannelException(channel)
        if not listeners:
            raise DispatcherException('invalid listener (None)!')

        listener = ActionListener()
        listener.channel = channel
        listener.listener = listeners
        listener.type = type

        with self._lock_channel_listeners:
            listeners = self._channel_listeners.get(channel)
            if not listeners:
                listeners = []
                self._channel_listeners[channel] = listeners
            listeners.append(listener)

    # pylint: disable=protected-access
    def register_cron_listener(self, cron_key: str, job: schedule.Job, listener):
        if job and listener:
            instance = self

            def job_closure():
                action = Action.create_cron_action(cron_key)
                action.listener = listener
                instance._action_queue.put(action)  # no protected access, just a closure

            job.do(job_closure)

    def push_action(self, root_action: Action) -> None:
        if not root_action or not root_action.is_valid():
            raise OhIllegalActionException(root_action)

        max_queued_actions = 1000
        count_queued_actions = self._action_queue.qsize()
        if count_queued_actions > max_queued_actions:
            raise DispatcherException('max queued actions exceeded ({} > {})!'
                                      .format(count_queued_actions, max_queued_actions))

        if root_action.listener is None:
            with self._lock_channel_listeners:
                listeners = self._channel_listeners.get(root_action.channel)
                if listeners:
                    for listener in listeners:
                        action = copy.deepcopy(root_action)
                        action.listener = listener.listener
                        self._action_queue.put(action)
        else:
            listener = root_action.listener
            root_action.listener = None
            action = copy.deepcopy(root_action)
            action.listener = listener
            root_action.listener = listener
            self._action_queue.put(action)

    def dispatch(self) -> bool:
        return self.dispatch_skip_cron(800)

    def dispatch_skip_cron(self, skip_cron_ms) -> bool:
        something_processed = False
        start_loop = True

        action = None
        while action or start_loop:
            start_loop = False
            try:
                action = self._action_queue.get_nowait()
            except Empty:
                action = None

            if self._dispatch_action(action):
                something_processed = True

        diff = datetime.datetime.now() - self._last_cron_run
        if diff.microseconds >= skip_cron_ms:
            self._last_cron_run = datetime.datetime.now()
            schedule.run_pending()

        return something_processed

    @staticmethod
    def _dispatch_action(action: Action) -> bool:
        """
        notify listener
        :return: True if a rule was found and executed (=> no extra sleep before the next execution
        """
        if action and action.listener:
            action_ident = str(action)
            try:
                time_start = datetime.datetime.now()

                action.listener.notify_action(action)
                # _logger.debug('dispatch_action(%s)', action_ident)

                diff_seconds = (datetime.datetime.now() - time_start).total_seconds()
                if diff_seconds > 0.5:
                    listener = str(action.listener)
                    _logger.warning('dispatch_action "%s:%s" took %.2fs', listener, action_ident, diff_seconds)

            except Exception as ex:
                _logger.error('error - dispatch_action(%s) failed! - (%s: %s)', action_ident, ex.__class__.__name__, ex)
                if not isinstance(ex, requests.exceptions.RequestException):
                    _logger.exception(ex)
            return True

        return False
