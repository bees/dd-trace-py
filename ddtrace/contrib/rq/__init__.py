"""
The RQ integration will trace worker execution.

TODO: example

If you only wish to patch some workers, you can patch individual workers with a
decorator or a patching method:

TODO: example
"""
from ..util import require_modules

required_modules = ['rq']

with require_modules(required_modules) as missing_modules:
    if not missing_modules:
        from .patch import patch, unpatch
        from .worker import patch_worker, unpatch_worker

        __all__ = [
            'patch',
            'unpatch',
            'patch_worker',
            'unpatch_worker',
       ]
