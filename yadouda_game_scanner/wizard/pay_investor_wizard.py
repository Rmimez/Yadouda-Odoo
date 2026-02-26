# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import _, models, fields, api
from odoo.exceptions import UserError


class YadoudaGamePayInvestorWizard(models.TransientModel):
    _name = 'yadouda.game.pay.investor.wizard'
    _description = 'Pay investor – select date range'

    game_id = fields.Many2one(
        'yadouda.game',
        string='Game',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    date_start = fields.Date(
        string='Start date',
        required=True,
        default=lambda self: self._default_previous_quarter_start(),
    )
    date_end = fields.Date(
        string='End date',
        required=True,
        default=lambda self: self._default_previous_quarter_end(),
    )
    line_ids = fields.Many2many(
        'yadouda.game.ticket.line',
        relation='yadouda_pay_wizard_ticket_line_rel',
        column1='wizard_id',
        column2='ticket_line_id',
        string='Ticket lines in range',
        compute='_compute_line_ids',
        store=True,
        readonly=True,
    )
    total_quantity = fields.Float(
        string='Total quantity',
        compute='_compute_totals',
        store=True,
        digits='Product Unit of Measure',
    )
    total_amount = fields.Float(
        string='Total amount',
        compute='_compute_totals',
        store=True,
        digits='Product Price',
    )
    currency_id = fields.Many2one(
        related='game_id.currency_id',
        readonly=True,
    )

    @api.model
    def _default_previous_quarter_start(self):
        """First day of the quarter before the current one (in user's timezone)."""
        today = fields.Date.context_today(self)
        quarter = (today.month - 1) // 3 + 1
        current_quarter_first = today.replace(day=1, month=(quarter - 1) * 3 + 1)
        return current_quarter_first - relativedelta(months=3)

    @api.model
    def _default_previous_quarter_end(self):
        """Last day of the quarter before the current one (in user's timezone)."""
        today = fields.Date.context_today(self)
        quarter = (today.month - 1) // 3 + 1
        current_quarter_first = today.replace(day=1, month=(quarter - 1) * 3 + 1)
        return current_quarter_first - relativedelta(days=1)

    @api.depends('date_start', 'date_end', 'game_id', 'game_id.ticket_line_ids', 'game_id.ticket_line_ids.date')
    def _compute_line_ids(self):
        for wiz in self:
            if not wiz.game_id:
                wiz.line_ids = self.env['yadouda.game.ticket.line']
                continue
            domain = [
                ('game_id', '=', wiz.game_id.id),
                ('date', '>=', wiz.date_start),
                ('date', '<=', wiz.date_end),
            ]
            wiz.line_ids = self.env['yadouda.game.ticket.line'].search(domain, order='date, id')

    @api.depends('line_ids', 'line_ids.quantity', 'line_ids.amount')
    def _compute_totals(self):
        for wiz in self:
            wiz.total_quantity = sum(wiz.line_ids.mapped('quantity'))
            wiz.total_amount = sum(wiz.line_ids.mapped('amount'))

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for wiz in self:
            if wiz.date_start and wiz.date_end and wiz.date_start > wiz.date_end:
                raise UserError(_('End date must be after or equal to start date.'))

    def action_create_bill(self):
        self.ensure_one()
        game = self.game_id
        if not game.investor_id:
            raise UserError(_('Please set an Investor on this game before paying.'))
        if not self.line_ids:
            raise UserError(_('There are no ticket lines between %s and %s.', self.date_start, self.date_end))

        journal = self.env['account.journal'].search([
            ('company_id', '=', game.company_id.id),
            ('type', '=', 'purchase'),
        ], limit=1)
        if not journal:
            raise UserError(_('No purchase journal found for company %s.', game.company_id.name))

        invoice_lines = []
        revenue_pct = (game.revenue_percentage or 0.0) / 100.0
        if revenue_pct <= 0 or revenue_pct > 1.0:
            revenue_pct = 0.5  # fallback 50%
        for line in self.line_ids:
            account = (
                line.product_id.property_account_expense_id
                or line.product_id.categ_id.property_account_expense_categ_id
            )
            if not account:
                raise UserError(_('Product %s has no expense account configured.', line.product_id.display_name))
            # Apply revenue percentage to quantity on the bill
            bill_quantity = line.quantity * revenue_pct
            invoice_lines.append((0, 0, {
                'display_type': 'product',
                'product_id': line.product_id.id,
                'name': line.product_id.display_name,
                'quantity': bill_quantity,
                'price_unit': line.unit_price,
                'account_id': account.id,
                'product_uom_id': line.product_id.uom_id.id,
            }))

        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': game.investor_id.id,
            'game_id': game.id,
            'journal_id': journal.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': invoice_lines,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'context': {'default_move_type': 'in_invoice'},
        }
