# stdlib
import os

# Third party
import wrapt

# Project
from ddtrace import Pin
from ddtrace.ext import AppTypes
from ddtrace.util import unwrap

APP = 'rq'
SERVICE = os.environ.get('DATADOG_SERVICE_NAME') or 'rq'

def patch_worker(worker):
    """ patch_worker will add tracing to a rq worker"""
    patch_methods = [
        ('__init__', _worker_init),
        ('work', _worker_execute_job),
    ]

    _w = wrapt.wrap_function_wrapper
    for method_name, wrapper in patch_methods:
        _w('rq.worker', 'Worker.{}'.format(method_name), wrapper)


# TODO: fixme, need to unpatch correctly
def unpatch_worker(worker):
    """ unpatch_worker will remove tracing from a rq worker"""
    patch_methods = [
        ('__init__', _worker_init),
        ('work', _worker_execute_job),
    ]
    for method_name, wrapper in patch_methods:
        # Get the wrapped method
        wrapper = getattr(worker, method_name, None)
        if wrapper is None:
            continue

        # Only unpatch if the wrapper is an `ObjectProxy`
        if not isinstance(wrapper, wrapt.ObjectProxy):
            continue

        # Restore original method
        unwrap(getattr(worker, method_name))


# TODO: determine how pin worker instances
def _worker_init(func, instance, args, kwargs):
    pin = Pin(service=SERVICE, app=APP, app_type=AppTypes.worker)


# TODO: determine metadata, how to extract pin
def _worker_execute_job(func, instance, args, kwargs):
    pin = Pin.get_from(instance)
    if not pin or not pin.enabled():
        return func(*args, **kwargs)

    with pin.tracer.trace('rq.worker', service=pin.service, span_type='rq') as span:
        span.set_meta('job_id', res.id)
        span.set_meta('state', res.state)
        return func(*args, **kwargs)
