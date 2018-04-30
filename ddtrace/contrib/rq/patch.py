# Third party
import rq

# Project
from worker import patch_worker, unpatch_worker

#TODO: add support for signals to handle dynamic worker registration
def patch():
    """ patch will add all available tracing to the rq library """
    setattr(rq, 'Worker', patch_worker(rq.Worker))


def unpatch():
    """ unpatch will remove tracing from the rq library """
    setattr(rq, 'Worker', unpatch_worker(rq.Worker))
