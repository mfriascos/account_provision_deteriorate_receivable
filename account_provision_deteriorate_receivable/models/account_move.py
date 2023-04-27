from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    deteriorate_date = fields.Date(
        string=_("Deteriorate Date")
    )
    provision_date = fields.Date(
        string=_("Provision Date")
    )
    deteriorate_percentage = fields.Float(
        string=_("Deteriorate Percentage")
    )
    provision_percentage = fields.Float(
        string=_("Provision Percentage")
    )
    deteriorate_amount = fields.Float(
        string=_("Deteriorate Amount")
    )
    provision_amount = fields.Float(
        string=_("Provision Amount")
    )
    invoice_id = fields.Many2one(
        'account.move',
        string="Invoice"
    )
    account_receivable_id = fields.Char(
        string="Receivable Account",
        related="partner_id.property_account_receivable_id.code",
        store="True")
    expired_days = fields.Integer(
        string="Expired Days",
        compute="_compute_expired_days")
    book_value_fiscal = fields.Float(
        string="Book value fiscal",
        compute="_compute_book_value_fiscal"
    )
    book_value_niif = fields.Float(
        string="Book value NIIF",
        compute="_compute_book_value_niif"
    )
    difference_niif_fiscal = fields.Float(
        string="Difference NIFF-Fiscal",
        compute="_compute_difference_niif_fiscal"
    )
    difference_niif_fiscal_value = fields.Float(
        string="Difference NIIF Fiscal Value",
        compute="_compute_difference_niif_fiscal_value"
    )

    selected_deteriorate = fields.Boolean(
        string="#",
    )

    is_provision_or_deterioration = fields.Boolean(
        string='Is provison or deteriorate',
        default=False,
    )

    @api.depends('invoice_date_due')
    def _compute_expired_days(self):
        for rec in self:
            rec.expired_days = 0
            if rec.invoice_date_due:
                expired_day = \
                    fields.Date.from_string(fields.Date.context_today(self))\
                    - fields.Date.from_string(rec.invoice_date_due)
                rec.expired_days = int(expired_day.days)

    @api.depends('amount_total', 'provision_amount')
    def _compute_book_value_fiscal(self):
        for rec in self:
            rec.book_value_fiscal = rec.amount_total - rec.provision_amount

    @api.depends('amount_total', 'deteriorate_amount')
    def _compute_book_value_niif(self):
        for rec in self:
            rec.book_value_niif = rec.amount_total - rec.deteriorate_amount

    @api.depends('deteriorate_amount', 'provision_amount')
    def _compute_difference_niif_fiscal(self):
        for rec in self:
            rec.difference_niif_fiscal = rec.deteriorate_amount\
                - rec.provision_amount

    @api.depends('book_value_fiscal', 'book_value_niif')
    def _compute_difference_niif_fiscal_value(self):
        for rec in self:
            rec.difference_niif_fiscal_value = rec.book_value_fiscal\
                - rec.book_value_niif
