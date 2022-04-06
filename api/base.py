import importlib
import traceback

import requests

from config import logging, LOGGER_CONFIG
from models import XRate, peewee_datetime, ApiLog, ErrorLog

fh = logging.FileHandler(LOGGER_CONFIG["file"])
fh.setLevel(LOGGER_CONFIG["level"])
fh.setFormatter(LOGGER_CONFIG["formatter"])


def update_rate(from_currency, to_currency):
    xrate = XRate.select().where(XRate.from_currency == from_currency,
                                 XRate.to_currency == to_currency).first()
    module = importlib.import_module(f"api.{xrate.module}")
    module.Api().update_rate(xrate)


class BaseApi:
    def __init__(self, logger_name):
        self.log = logging.getLogger(logger_name)
        self.log.addHandler(fh)
        self.log.setLevel(LOGGER_CONFIG["level"])

    def update_rate(self, xrate):
        self.log.info("Started update for: %s" % xrate)
        self.log.debug("rate before: %s", xrate)
        xrate.rate = self._update_rate(xrate)
        xrate.updated = peewee_datetime.datetime.now()
        xrate.save()

        self.log.debug("rate after: %s", xrate)
        self.log.info("Finished update for: %s" % xrate)

    def _update_rate(self, xrate):
        raise NotImplementedError("_update_rate")

    def _send_request(self, url, method, data=None, headers=None):
        api_log = ApiLog(request_url=url, request_data=data, request_method=method,
                         request_headers=headers)
        try:
            response = self._send(method=method, url=url, headers=headers, data=data)
            api_log.response_text = response.text
            return response
        except Exception as ex:
            self.log.exception("Error request")
            api_log.error = str(ex)
            ErrorLog.create(request_data=data, request_url=url, request_method=method, error=str(ex),
                            traceback=traceback.format_exc(chain=False))
            raise
        finally:
            api_log.finished = peewee_datetime.datetime.now()
            api_log.save()

    def _send(self, url, method, data=None, headers=None):
        return requests.request(method=method, url=url, headers=headers, data=data, timeout=15)
