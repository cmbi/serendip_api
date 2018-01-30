import logging

from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object


_log = logging.getLogger(__name__)


def run(url, timeout, method, *args):
    transport = Transport(timeout=timeout)
    client = Client(url, transport=transport)

    _log.info("Running '{}' on url '{}' with arguments: {}".format(method, url, args))
    response = getattr(client.service, method)(*args)
    _log.info("Finished running '{}' on url '{}'".format(method, url))

    return serialize_object(response)
