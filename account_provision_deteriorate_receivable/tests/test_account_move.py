from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError
from odoo.tests.common import TransactionCase

# Review SavePoint implementation and SingleTransaction


class TestAccountMove(TransactionCase):

    def setUp(self):
        super(TestAccountMove, self).setUp()
        self.account_move = self.env['account.move']
        self.account_journal = self.env['account.journal']
        self.res_partner = self.env['res.partner']

        self.partner_1 = self.res_partner.create({
            "name": "Bits"
        })

        self.journal_1 = self.account_journal.create({
            "name": "Journal",
            "type": "sale",
            "code": "123"
        })

        self.move_1 = self.account_move.create({
            "name": "Test",
            "journal_id": self.journal_1.id,
            "partner_id": self.partner_1.id,
            "invoice_date_due": date(2020, 1, 1),
            "deteriorate_date": date(2017, 3, 1),
            "provision_date": date(2017, 3, 1),
            "deteriorate_amount": 120,
            "provision_amount": 120
        })

    def test_compute_expired_days(self):
        self.move_1._compute_expired_days()
        self.move_1.write({"invoice_date_due": False})
        self.move_1._compute_expired_days()

    def test_compute_book_value_fiscal(self):
        self.move_1._compute_book_value_fiscal()

    def test_compute_book_value_niif(self):
        self.move_1._compute_book_value_niif()

    def test_compute_difference_niif_fiscal(self):
        self.move_1._compute_difference_niif_fiscal()

    def test_compute_difference_niif_fiscal_value(self):
        self.move_1._compute_difference_niif_fiscal_value()
