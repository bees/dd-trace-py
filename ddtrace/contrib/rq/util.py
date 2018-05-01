# stdlib
import os

# Project
from ddtrace import Pin

APP = 'rq'
SERVICE = os.environ.get('DATADOG_SERVICE_NAME') or 'rq'


def require_pin(decorated):
    """ decorator for extracting the `Pin` from a wrapped method """
    def _wrapper(wrapped, instance, args, kwargs):
        pin = Pin.get_from(instance)
        # Execute the original method if pin is not enabled
        if not pin or not pin.enabled():
            return wrapped(*args, **kwargs)

        # Execute our decorated function
        return decorated(pin, wrapped, instance, args, kwargs)
    return _wrapper
