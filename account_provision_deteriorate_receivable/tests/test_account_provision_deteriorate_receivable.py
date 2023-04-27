from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError
from odoo.tests.common import TransactionCase

# Review SavePoint implementation and SingleTransaction


class TestAccountProvisionDeteriorateReceivable(TransactionCase):

    def setUp(self):
        super(TestAccountProvisionDeteriorateReceivable, self).setUp()
        self.account_account = self.env['account.account']
        self.account_type = self.env['account.account.type']
        self.account_move = self.env['account.move']
        self.account_analytic_account = self.env['account.analytic.account']
        self.account_journal = self.env['account.journal']
        self.res_partner = self.env['res.partner']
        self.product_product = self.env['product.product']
        self.product_category = self.env['product.category']
        self.res_cunrrency = self.env['res.currency'].search([])[0]
        self.receivable_settings = self.env[
            'account.provision.deteriorate.receivable.settings']
        self.receivable = self.env[
            'account.provision.deteriorate.receivable']

        self.account_type1 = self.account_type.search([])
        self.liquidity_type_id = self.env.ref(
            'account.data_account_type_liquidity')

        self.account_account1 = self.account_account.new({
            'code': '1',
            'name': 'Test Acount 1',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account12 = self.account_account.new({
            'code': '12',
            'name': 'Test Acount 12',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account4 = self.account_account.new({
            'code': '4',
            'name': 'Test Acount 4',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account42 = self.account_account.new({
            'code': '42',
            'name': 'Test Acount 4',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account5 = self.account_account.new({
            'code': '5',
            'name': 'Test Acount 5',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account52 = self.account_account.new({
            'code': '5',
            'name': 'Test Acount 5',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account6 = self.account_account.new({
            'code': '6',
            'name': 'Test Acount 6',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account6 = self.account_account.new({
            'code': '62',
            'name': 'Test Acount 6',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account7 = self.account_account.new({
            'code': '7',
            'name': 'Test Acount 7',
            'user_type_id': self.liquidity_type_id
        })
        self.account_account72 = self.account_account.new({
            'code': '72',
            'name': 'Test Acount 72',
            'user_type_id': self.liquidity_type_id
        })

        # Test functionality
        self.partner = self.res_partner.create({
            'name': 'partner name'
        })
        self.account_bank = self.account_account.search([])
        self.journal_bank = self.account_journal.create({
            "name": "Test Bank",
            "code": "TESB",
            "type": "general",
            'default_credit_account_id': self.account_account72.id,
            'default_debit_account_id':  self.account_account72.id
        })
        self.account_journal_1 = self.account_journal.create({
            "name": "Test",
            "code": "TEST1",
            "type": "purchase"
        })
        self.account_journal_2 = self.env['account.journal'].create({
            "name": "Test",
            "code": "TEST2",
            "type": "sale"
        })
        self.category_one = self.product_category.create({
            'name': 'All',
        })
        self.product_one = self.product_product.create({
            'name': 'product one',
            'categ_id': self.category_one.id,
            'type': 'consu',
            'lst_price': 10,
            'standard_price': 8,
            'sale_ok': True,
            'purchase_ok': True
        })
        self.account_1 = self.account_account.create({
            'name': 'Test Account 1',
            'code': '51236877',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_payable').id
        })
        self.account_2 = self.account_account.create({
            'name': 'Test Account 2',
            'code': '51236883',
            'user_type_id': self.env.ref(
                'account.data_account_type_liquidity').id
        })
        self.account_3 = self.account_account.create({
            'name': 'Test Account 1',
            'code': '51236887',
            'user_type_id': self.env.ref(
                'account.data_account_type_current_assets').id
        })

        self.account_analytic_account_1 = self.account_analytic_account.new({
            'name': 'Test Acount 1',
        })

        self.payment_term = self.env.ref('account.account_payment_term_30days')

        self.move_1 = {
            'journal_id': self.account_journal_1.id,
            'invoice_date': date(2020, 1, 1),
            'invoice_date_due': date(2020, 1, 1),
            'date': date(2020, 1, 1),
            'type': 'entry',
            'type_name': 'Invoice',
            'selected_deteriorate': True,
            'invoice_payment_term_id': self.payment_term.id,
            'line_ids': [(0, 0, {
                'account_id': self.account_2.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2020, 1, 1),
                'credit': 0.0,
                'debit': 1000.0
            }), (0, 0, {
                'account_id': self.account_1.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2020, 1, 1),
                'credit': 1000.0,
                'debit': 0.0
            })]
        }

        self.move_2 = {
            'journal_id': self.account_journal_1.id,
            'invoice_date': date(2018, 9, 17),
            'invoice_date_due': date(2020, 9, 17),
            'partner_id': self.partner.id,
            'date': date(2020, 9, 17),
            'type': 'in_invoice',
            'type_name': 'Invoice',
            'selected_deteriorate': True,
            'line_ids': [(0, 0, {
                'account_id': self.account_2.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2020, 1, 1),
                'credit': 0.0,
                'debit': 1000.0
            }), (0, 0, {
                'account_id': self.account_1.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2020, 1, 1),
                'credit': 1000.0,
                'debit': 0.0
            })]
        }

        self.move_3 = {
            'journal_id': self.account_journal_2.id,
            'invoice_date': date(2021, 11, 1),
            'invoice_date_due': date(2021, 12, 31),
            'partner_id': self.partner.id,
            'date': date(2021, 11, 1),
            'type': 'out_invoice',
            'type_name': 'Invoice',
            'selected_deteriorate': True,
            'invoice_payment_term_id': self.payment_term.id,
            'line_ids': [(0, 0, {
                'account_id': self.account_2.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2021, 11, 1),
                'credit': 0.0,
                'debit': 1000.0
            }), (0, 0, {
                'account_id': self.account_1.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2021, 11, 1),
                'credit': 1000.0,
                'debit': 0.0
            })]
        }

        self.move_4 = {
            'journal_id': self.account_journal_2.id,
            'invoice_date': date(2021, 11, 1),
            'invoice_date_due': date(2021, 12, 31),
            'partner_id': self.partner.id,
            'date': date(2021, 11, 1),
            'type': 'out_invoice',
            'type_name': 'Invoice',
            'selected_deteriorate': True,
            'line_ids': [(0, 0, {
                'account_id': self.account_2.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2021, 11, 1),
                'credit': 0.0,
                'debit': 1000.0
            }), (0, 0, {
                'account_id': self.account_1.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2021, 11, 1),
                'credit': 1000.0,
                'debit': 0.0
            })]
        }

        self.move_5 = {
            'journal_id': self.account_journal_2.id,
            'partner_id': self.partner.id,
            'date': date(2021, 11, 1),
            'type': 'out_invoice',
            "invoice_line_ids": [(0, 0, {
                'product_id': self.product_one.id,
                'account_id': self.account_3.id,
                'quantity': 2.0,
                'price_unit': 1000,
            })],
            'line_ids': [(0, 0, {
                'account_id': self.account_2.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2021, 11, 1),
                'credit': 0.0,
                'debit': 1000.0
            }), (0, 0, {
                'account_id': self.account_1.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2021, 11, 1),
                'credit': 1000.0,
                'debit': 0.0
            })]
        }

        self.move_6 = {
            'journal_id': self.account_journal_2.id,
            'invoice_date': date(2021, 11, 1),
            'invoice_date_due': date(2021, 12, 31),
            'partner_id': self.partner.id,
            'date': date(2021, 11, 1),
            'type': 'out_invoice',
            'type_name': 'Invoice',
            'selected_deteriorate': False,
            'line_ids': [(0, 0, {
                'account_id': self.account_2.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2021, 11, 1),
                'credit': 0.0,
                'debit': 1000.0
            }), (0, 0, {
                'account_id': self.account_1.id,
                'partner_id': self.partner.id,
                'analytic_account_id': self.account_analytic_account_1.id,
                'date': date(2021, 11, 1),
                'credit': 1000.0,
                'debit': 0.0
            })]
        }

        self.receivable_settings_1 = self.receivable_settings.create({
            'accounting_type': 'niif',
            'percentage': '0.02',
            'first_day': '121',
            'number_days': '1',
            'expense_account_id': self.account_1.id,
            'accumulation_account_id': self.account_2.id,
            'recovery_account_id': self.account_3.id,
            'journal_id': self.account_journal_1.id
        })
        self.receivable_settings_1 = self.receivable_settings.create({
            'accounting_type': 'fiscal',
            'percentage': '33',
            'first_day': '361',
            'number_days': '360',
            'expense_account_id': self.account_1.id,
            'accumulation_account_id': self.account_2.id,
            'recovery_account_id': self.account_3.id,
            'journal_id': self.account_journal_1.id
        })

    def test_execute_process(self):
        receivable_1 = self.receivable.create({
            'execute_type': 'all',
            'execute_type_niif': False,
            'execute_date': date(2021, 2, 1)
        })
        move_1 = self.account_move.create(self.move_1)
        move_1.post()
        move_1.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        move_1.read([])
        move_2 = self.account_move.create(self.move_2)
        move_2.post()
        move_2.write({
            'invoice_payment_state': 'not_paid',
        })
        move_3 = self.account_move.create(self.move_3)
        move_3.post()
        move_3.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        move_4 = self.account_move.create(self.move_4)
        move_4.post()
        move_4.write({
            'invoice_payment_state': 'not_paid',
        })
        move_5 = self.account_move.create(self.move_5)
        move_5.post()
        move_5.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        move_6 = self.account_move.create(self.move_6)
        move_6.post()
        move_6.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        self.payment_term.line_ids[0].read([])
        receivable_1.execute_filter()
        receivable_1.select_all()
        receivable_1.execute_process()

    def test_execute_process_less_count(self):
        receivable_1 = self.receivable.create({
            'execute_type': 'all',
            'execute_type_niif': False,
            'execute_date': date(2021, 2, 1)
        })
        move_1 = self.account_move.create(self.move_1)
        move_1.post()
        move_1.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        move_1.read([])
        move_2 = self.account_move.create(self.move_2)
        move_2.post()
        move_2.write({
            'invoice_payment_state': 'not_paid',
        })
        move_3 = self.account_move.create(self.move_3)
        move_3.post()
        move_3.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        move_4 = self.account_move.create(self.move_4)
        move_4.post()
        move_4.write({
            'invoice_payment_state': 'not_paid',
        })
        move_5 = self.account_move.create(self.move_5)
        move_5.post()
        move_5.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        receivable_1.execute_filter()
        receivable_1.move_ids[0].write({
            'invoice_date': date(2021, 2, 1),
            'invoice_date_due': date(2021, 2, 1)
        })
        receivable_1.select_all()
        receivable_1.execute_process()

    def test_error_wizard(self):
        receivable_1 = self.receivable.create({
            'execute_type': 'all',
            'execute_type_niif': False,
            'execute_date': date(2021, 2, 1)
        })
        receivable_1.write({
            'execute_date': False
        })

        move_1 = self.account_move.create({
            'journal_id': self.journal_bank.id,
            'invoice_date': date(2020, 1, 1),
            'invoice_date_due': date(2020, 1, 1),
            'date': date(2020, 1, 1),
            'type': 'entry',
            'invoice_payment_term_id': self.payment_term.id,
            'invoice_payment_state': 'not_paid',
            'line_ids': [(0, 0, {
                'account_id': self.account_2.id,
                'partner_id': self.partner.id,
                'date': date(2020, 1, 1),
                'credit': 0.0,
                'debit': 1000.0
            }), (0, 0, {
                'account_id': self.account_1.id,
                'partner_id': self.partner.id,
                'date': date(2020, 1, 1),
                'credit': 1000.0,
                'debit': 0.0
            })]
        })
        move_1.post()
        move_2 = self.account_move.create(self.move_2)
        move_2.post()
        move_2.write({
            'invoice_payment_state': 'not_paid',
        })
        move_3 = self.account_move.create(self.move_3)
        move_3.post()
        move_3.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        move_4 = self.account_move.create(self.move_4)
        move_4.post()
        move_4.write({
            'invoice_payment_state': 'not_paid',
        })
        move_5 = self.account_move.create(self.move_5)
        move_5.post()
        move_5.write({
            'invoice_payment_state': 'not_paid',
            'amount_residual': 4610.0,
        })
        receivable_1.execute_filter()
