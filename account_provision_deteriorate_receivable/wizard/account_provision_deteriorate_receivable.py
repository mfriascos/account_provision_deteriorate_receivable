from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import math


class AccountProvisionDeteriorateReceivable(models.TransientModel):
    _name = 'account.provision.deteriorate.receivable'
    _rec_name = 'execute_date'
    execute_type = fields.Selection(
        [
            ("niif", _("NIIF")),
            ("fiscal", _("FISCAL")),
            ("all", _("All"))
        ],
        string=_("Execute Type"),
        required=True
    )
    execute_type_niif = fields.Selection(
        [
            ("interest_rate", _("Interest Rate")),
            ("all", _("100% CXC"))
        ],
        string=_("Execute Type NIIF")
    )
    execute_date = fields.Date(
        string=_("Execute Date")
    )
    move_ids = fields.Many2many(
        "account.move",
        string=_("Invoices"),
        required=True
    )
    receivable_settings_ids = dict()
    rules = []

    def execute_filter(self):
        for record in self:
            record.move_ids.write({'selected_deteriorate': False})
            record.move_ids = False
            if record.execute_type and record.execute_date:
                record._get_provision_deteriorate_settings()
                invoices_result = record._execute_query()
                invoice_ids = []
                record.rules = []
                for invoice in invoices_result:
                    ban = record._create_settings_filters(invoice)
                    if ban:
                        invoice_ids.append(invoice.get("id", False))
                record.move_ids = self.env["account.move"].browse(invoice_ids)\
                    if invoice_ids else False

    def _get_provision_deteriorate_settings(self):
        accounting_type = [] if self.execute_type == "all" else \
            [('accounting_type', '=', self.execute_type)]
        receivable_settings \
            = self.env['account.provision.deteriorate.receivable.settings'].\
            search(accounting_type)
        self.receivable_settings_ids = dict()
        for rule in receivable_settings:
            self.receivable_settings_ids[rule.accounting_type] = {
                "accounting_type": rule.accounting_type,
                "percentage": (100 if self.execute_type_niif == 'all'
                               else rule.percentage),
                "first_day": rule.first_day,
                "number_days": rule.number_days,
                "expense_account_id": rule.expense_account_id,
                "accumulation_account_id": rule.accumulation_account_id,
                "recovery_account_id": rule.recovery_account_id,
                "journal_id": rule.journal_id
            }

    def _create_settings_filters(self, invoice):
        ban = False
        count = invoice.get("count", 0)
        invoice['count'] = 0 if type(count) != int and type(count) != float\
            else count
        for rule in self.receivable_settings_ids.values():
            if invoice.get("count", 0) >= rule.get('first_day', 0):
                self.rules.append({
                    "id": invoice.get("id", False),
                    "count": invoice.get("count", 0),
                    "accounting_type": rule.get('accounting_type', False),
                    "percentage": rule.get('percentage', 0),
                    "number_days": rule.get('number_days', 0),
                    "first_day": rule.get('first_day', 0),
                    "expense_account_id": rule.get(
                        'expense_account_id', False),
                    "accumulation_account_id": rule.get(
                        'accumulation_account_id', False),
                    "recovery_account_id": rule.get(
                        'recovery_account_id', False),
                    "journal_id": rule.get('journal_id', False),
                })
                ban = True
        return ban

    def _get_count_days(self, invoice):
        count = False
        limit_date = False
        if invoice.invoice_payment_term_id:
            limit_date = invoice.invoice_date \
                + timedelta(
                    days=invoice.invoice_payment_term_id.line_ids[0].days)
        else:
            limit_date = invoice.invoice_date_due
        count = self.execute_date - limit_date
        count = count.days
        return count

    def _get_process_to_do(self, invoice):
        process = []
        for rule in self.receivable_settings_ids.values():
            count = self._get_count_days(invoice)
            if count >= rule.get('first_day', 0):
                process.append({
                    "id": invoice.id,
                    "count": count - rule.get('first_day', 0) + 1,
                    "accounting_type": rule.get('accounting_type', False),
                    "percentage": rule.get('percentage', 0),
                    "number_days": rule.get('number_days', 0),
                    "first_day": rule.get('first_day', 0),
                    "expense_account_id": rule.get(
                        'expense_account_id', False),
                    "accumulation_account_id": rule.get(
                        'accumulation_account_id', False),
                    "recovery_account_id": rule.get(
                        'recovery_account_id', False),
                    "journal_id": rule.get('journal_id', False),
                })
        return process

    def _create_journal_items(self, process, invoice, amount):
        journal_items = []
        values = dict()
        values["partner_id"] = invoice.company_id.id
        values["account_id"] = process.get('expense_account_id', False).id
        values["debit"] = amount
        values["credit"] = 0
        values["name"] = _("PROVISION RECEIVABLE (FISCAL)") if\
            process.get("accounting_type", False) == "fiscal" else\
            _("DETERIORATE RECEIVABLE (NIIF)")
        journal_items.append((0, 0, values))
        values = dict()
        values["partner_id"] = invoice.company_id.id
        values["account_id"] = process.get('accumulation_account_id', False).id
        values["debit"] = 0
        values["credit"] = amount
        values["name"] = _("PROVISION RECEIVABLE (FISCAL)") if\
            process.get("accounting_type", False) == "fiscal" else\
            _("DETERIORATE RECEIVABLE (NIIF)")
        journal_items.append((0, 0, values))
        return journal_items

    def _get_taken_data(self, process, invoice, percentage, amount):
        if process.get('accounting_type') == 'fiscal':
            invoice.provision_date = self.execute_date
            new_percentage = percentage - (
                0 if not invoice.provision_percentage
                else invoice.provision_percentage)
            invoice.provision_percentage = percentage
            new_amount = amount - (
                0 if not invoice.provision_amount
                else invoice.provision_amount)
            invoice.provision_amount = amount
        else:
            invoice.deteriorate_date = self.execute_date
            new_percentage = percentage - (
                0 if not invoice.deteriorate_percentage
                else invoice.deteriorate_percentage)
            invoice.deteriorate_percentage = percentage
            new_amount = amount - (
                0 if not invoice.deteriorate_amount
                else invoice.deteriorate_amount)
            invoice.deteriorate_amount = amount
        return new_percentage, new_amount

    def _create_journal_entry(self, process, invoice, percentage, amount):
        ref = _('PROVISION RECEIVABLE') if\
            process.get('accounting_type', False) ==\
            'fiscal' else _('DETERIORATE RECEIVABLE')
        ref += ' (' + str(self.execute_date) + ')'
        return {
            'ref': ref,
            'journal_id': process.get('journal_id', False).id,
            'company_id': invoice.company_id.id,
            'invoice_id': process.get('id', False),
            'is_provision_or_deterioration': True,
        }

    def _check_draft_moves(self):
        draft_entries = False
        for move in self.move_ids:
            draft_entries = self.env['account.move'].search([
                ('invoice_id', '=', move.id),
                ('state', '=', 'draft'),
                ('is_provision_or_deterioration', '=', True),
            ])

            if draft_entries:
                raise ValidationError(
                    _('The process cannot be executed because there are '
                      'draft entries related to provision or impairment.'))

    def execute_process(self):
        self._check_draft_moves()
        self._get_provision_deteriorate_settings()
        ids = []
        for invoice in self.move_ids:

            # Get settings
            settings = self._get_process_to_do(invoice)
            if invoice.selected_deteriorate:
                for process in settings:
                    # Calc percentage and amount
                    number_periods = math.ceil(
                        process.get("count", 0) /
                        process.get("number_days", 0))

                    percentage = number_periods * process.get('percentage', 0)
                    percentage = 100 if percentage > 100 else percentage
                    percentage_niif = (
                        1 + process.get('percentage', 0) / 100)\
                        ** number_periods
                    percentage_niif = 100 if percentage_niif > 100 \
                        else percentage_niif

                    if (process.get('accounting_type') == 'niif' and
                            process.get('percentage', 0) != 100):
                        percentage = percentage_niif
                        deteriorate_amount = (
                            invoice.amount_residual * percentage)\
                            - invoice.amount_residual
                        amount = deteriorate_amount
                        percentage = (percentage - 1) * 100
                    else:
                        amount = invoice.amount_residual * percentage / 100

                    # Calc percentage and amount already taken
                    percentage, amount = self._get_taken_data(
                        process, invoice, percentage, amount)

                    # Create journal entries and items
                    if amount > 0:
                        line_ids = self._create_journal_items(
                            process, invoice, amount)
                        journal_entry = self._create_journal_entry(
                            process, invoice, percentage, amount)
                        journal_entry['line_ids'] = line_ids
                        journal_entry = self.env['account.move'].create(
                            journal_entry)
                        partner_id = invoice.partner_id.id

                        for entry_line in invoice.line_ids:
                            analytic_account_id = \
                                entry_line.analytic_account_id.id
                            if analytic_account_id:
                                break
                        journal_entry.partner_id = partner_id

                        for entry_line in journal_entry.line_ids:
                            entry_line.partner_id = partner_id
                            if entry_line.account_id.code[0] in\
                                    ["4", "5", "6"]:
                                entry_line.analytic_account_id = \
                                    analytic_account_id

                        ids.append(journal_entry.id)

        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.move',
            'view_id': self.env.ref('account.view_move_tree').id,
            'domain': [('id', 'in', ids)]
        }

    # Create query
    def _execute_query(self):
        sql_select = self._get_sql_select()
        sql_from = self._get_sql_from()
        sql_where, params = self._get_sql_where()
        self.env.cr.execute(
            sql_select +
            sql_from +
            sql_where, params)
        results = self.env.cr.dictfetchall()
        return results

    def _get_sql_select(self):
        sql_select = """
            SELECT
                a.id
                , a.name
                , a.invoice_payment_term_id
                , a.invoice_date
                , a.amount_residual
                , c.days
                , a.invoice_date_due
                , DATE_PART(
                    'day',
                    %s - CASE
                        WHEN a.invoice_payment_term_id IS NOT NULL
                            THEN a.invoice_date + interval '1' day * c.days
                        ELSE a.invoice_date_due
                    END
                ) count
            """
        return sql_select

    def _get_sql_from(self):
        sql_from = """
            FROM
                account_move a
            LEFT JOIN
                account_payment_term b ON a.invoice_payment_term_id = b.id
            LEFT JOIN
                account_payment_term_line c ON c.payment_id = b.id
            """
        return sql_from

    def _get_sql_where(self):
        sql_where = """
            WHERE
                a.state = %s
                AND a.invoice_payment_state = %s
            """
        params = [
            self.execute_date,
            'posted',
            'not_paid'
        ]
        return sql_where, params

    def select_all(self):
        self.move_ids.write({'selected_deteriorate': True})
