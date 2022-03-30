import json
import unittest
from unittest.mock import patch

import api.cbr_api as cbr_api
import api.privat_api as privat_api
import models


def get_privat_response(*args, **kwargs):
    class Response:
        def __init__(self, response):
            self.text = json.dumps(response)

        def json(self):
            return json.loads(self.text)

    return Response([{"ccy": "USD", "base_ccy": "UAH", "sale": "30.0"}])


class Test(unittest.TestCase):
    def setUp(self) -> None:
        models.init_db()

    def tearDown(self) -> None:
        models.XRate.truncate_table()
        models.ApiLog.truncate_table()
        models.ErrorLog.truncate_table()

    # @classmethod
    # def setUpClass(cls) -> None:
    #     cls.init_db()

    # @classmethod
    # def tearDownClass(cls) -> None:
    #     cls.drop_db()
    #
    # @staticmethod
    # def init_db():
    #     models.XRate.create_table()
    #     models.XRate.create(from_currency=840, to_currency=980, rate=1)
    #     models.XRate.create(from_currency=840, to_currency=643, rate=1)
    #     print("db created!")
    #
    # @staticmethod
    # def drop_db():
    #     models.XRate.truncate_table()

    # def test_privat(self):
    #     xrate = models.XRate.get(from_currency=840, to_currency=980)
    #     updated_before = xrate.updated
    #     self.assertEqual(xrate.rate, 1.0)
    #     privat_api.Api().update_rate(840, 980)
    #     xrate = models.XRate.get(from_currency=840, to_currency=980)
    #     updated_after = xrate.updated
    #
    #     self.assertGreater(xrate.rate, 25)
    #     self.assertGreater(updated_after, updated_before)
    #
    #     api_log = models.ApiLog.select().order_by(models.ApiLog.created.desc()).first()
    #     self.assertIsNotNone(api_log)
    #     self.assertEqual(api_log.request_url, "https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11")
    #     self.assertIn('{"ccy":"USD","base_ccy":"UAH",', api_log.response_text)

    def test_cbr(self):
        xrate = models.XRate.get(from_currency=840, to_currency=643)
        updated_before = xrate.updated
        self.assertEqual(xrate.rate, 1.0)
        cbr_api.Api().update_rate(840, 643)
        xrate = models.XRate.get(from_currency=840, to_currency=643)
        updated_after = xrate.updated

        self.assertGreater(xrate.rate, 60)
        self.assertGreater(updated_after, updated_before)

        api_log = models.ApiLog.select().order_by(models.ApiLog.created.desc()).first()
        self.assertIsNotNone(api_log)
        self.assertEqual(api_log.request_url, "http://www.cbr.ru/scripts/XML_daily.asp")
        self.assertIn("<NumCode>840</NumCode>", api_log.response_text)

    @patch('api.base.BaseApi._send', new=get_privat_response)
    def test_privat_mock(self):
        xrate = models.XRate.get(from_currency=840, to_currency=980)
        updated_before = xrate.updated
        self.assertEqual(xrate.rate, 1.0)
        privat_api.Api().update_rate(840, 980)
        xrate = models.XRate.get(from_currency=840, to_currency=980)
        updated_after = xrate.updated

        self.assertGreater(xrate.rate, 25)
        self.assertGreater(updated_after, updated_before)

        api_log = models.ApiLog.select().order_by(models.ApiLog.created.desc()).first()
        self.assertIsNotNone(api_log)
        self.assertEqual(api_log.request_url, "https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11")
        self.assertIsNotNone(api_log.response_text)

        self.assertEqual('[{"ccy": "USD", "base_ccy": "UAH", "sale": "30.0"}]', api_log.response_text)


if __name__ == "__main__":
    unittest.main()
