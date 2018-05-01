# Third party
import wrapt

# Project
from ddtrace import Pin
from ddtrace.ext import AppTypes
from ddtrace.util import unwrap
from .util import (
    require_pin,
    APP,
    SERVICE,
)

# Note: this is essentially a direct port of the Celery contrib module


def patch_worker(worker, pin=None):
    """ patch_worker will add tracing to a rq worker"""
    patch_methods = [
        ('__init__', _worker_init),
        ('work', _worker_execute_job),
    ]

    _w = wrapt.wrap_function_wrapper
    for method_name, wrapper in patch_methods:
        method = getattr(worker, method_name, None)
        if method is None:
            continue

        # Do not patch if method is already patched
        if isinstance(method, wrapt.ObjectProxy):
            continue

        # Patch the method
        setattr(worker, method_name, wrapt.BoundFunctionWrapper(method, worker, wrapper))

    pin = pin or Pin(service=SERVICE, app=APP, app_type=AppTypes.worker)
    pin.onto(worker)
    return worker


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
        setattr(worker, method_name, wrapper.__wrapped__)


def _worker_init(func, instance, args, kwargs):
    func(*args, **kwargs)

    # Patch only if pin is enabled
    pin = Pin.get_from(instance)
    if pin and pin.enabled():
        patch_worker(instance, pin=pin)


@require_pin
def _worker_execute_job(pin, func, _instance, args, kwargs):
    job, queue = args
    with pin.tracer.trace('rq.worker', service=pin.service, span_type='rq') as span:
        span.set_meta('job_id', job.id)
        span.set_meta('queue_name', queue.name)
        return func(*args, **kwargs)
