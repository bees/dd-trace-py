import ddtrace
import tornado

from wrapt import wrap_function_wrapper as _w

from . import handlers, application, decorators, template, futures, compat, context_provider
from ...util import unwrap as _u


def patch():
    """
    Tracing function that patches the Tornado web application so that it will be
    traced using the given ``tracer``.
    """
    # patch only once
    if getattr(tornado, '__datadog_patch', False):
        return
    setattr(tornado, '__datadog_patch', True)

    # patch Application to initialize properly our settings and tracer
    _w('tornado.web', 'Application.__init__', application.tracer_config)

    # patch RequestHandler to trace all Tornado handlers
    _w('tornado.web', 'RequestHandler._execute', handlers.execute)
    _w('tornado.web', 'RequestHandler.on_finish', handlers.on_finish)
    _w('tornado.web', 'RequestHandler.log_exception', handlers.log_exception)

    # patch Template system
    _w('tornado.template', 'Template.generate', template.generate)

    # patch Python Futures when an Executor pool is used
    # TODO: this may be a generic module and should be moved
    # in a separate contributions when we want to support multi-threading
    # context propagation
    if compat.futures_available:
        _w('concurrent.futures', 'ThreadPoolExecutor.submit', futures._wrap_submit)

    # configure the global tracer
    ddtrace.tracer.configure(
        context_provider=context_provider,
        wrap_executor=decorators.wrap_executor,
    )


def unpatch():
    """
    Remove all tracing functions in a Tornado web application.
    """
    if not getattr(tornado, '__datadog_patch', False):
        return
    setattr(tornado, '__datadog_patch', False)

    # unpatch Tornado
    _u(tornado.web.RequestHandler, '_execute')
    _u(tornado.web.RequestHandler, 'on_finish')
    _u(tornado.web.RequestHandler, 'log_exception')
    _u(tornado.web.Application, '__init__')
    _u(tornado.concurrent, 'run_on_executor')
    _u(tornado.template.Template, 'generate')

    if compat.futures_available:
        _u('concurrent.futures.ThreadPoolExecutor', 'submit')
