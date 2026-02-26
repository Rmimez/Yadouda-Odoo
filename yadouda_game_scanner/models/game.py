# -*- coding: utf-8 -*-

from odoo import _, models, fields, api
from odoo.exceptions import UserError


class YadoudaGame(models.Model):
    _name = 'yadouda.game'
    _inherit = ['image.mixin']
    _description = 'Park Game'
    _rec_name = 'name'

    name = fields.Char(string='Game Name', required=True)
    code = fields.Char(string='Game Code', required=True, help='Short code for scanning')
    active = fields.Boolean(string='Active', default=True)
    investor_id = fields.Many2one(
        'res.partner',
        string='Investor',
        help='Investor or partner associated with this game.',
    )

    # Assign responsible users
    responsible_user_ids = fields.Many2many(
        'res.users',
        string='Game Operators',
        domain=[('share', '=', False)]  # Internal users only
    )

    # Current consumption tracking (computed so "today" is evaluated at read time)
    today_consumption_ids = fields.Many2many(
        'ticket.consumption',
        string="Today's Consumption",
        compute='_compute_today_consumption',
        compute_sudo=False,
    )
    today_total_tickets = fields.Integer(
        string="Today's Tickets",
        compute='_compute_today_totals'
    )

    # Bulk ticket entry (lines with date, product, quantity, total)
    ticket_line_ids = fields.One2many(
        'yadouda.game.ticket.line',
        'game_id',
        string='Bulk ticket lines',
    )
    total_bulk_quantity = fields.Float(
        string='Total quantity',
        compute='_compute_bulk_totals',
        digits='Product Unit of Measure',
    )
    total_bulk_amount = fields.Float(
        string='Total amount',
        compute='_compute_bulk_totals',
        digits='Product Price',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    investor_bill_ids = fields.One2many(
        'account.move',
        'game_id',
        string='Investor bills',
        domain=[('move_type', '=', 'in_invoice')],
        readonly=True,
    )
    investor_bill_count = fields.Integer(
        string='Bills count',
        compute='_compute_investor_bill_count',
    )

    @api.depends('investor_bill_ids')
    def _compute_investor_bill_count(self):
        for game in self:
            game.investor_bill_count = len(game.investor_bill_ids)

    def _compute_today_consumption(self):
        today = fields.Date.context_today(self)
        for game in self:
            game.today_consumption_ids = self.env['ticket.consumption'].search([
                ('game_id', '=', game.id),
                ('date', '=', today),
            ])

    # Scanner button action
    def action_open_scanner(self):
        """Open scanner interface for this game"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/yadouda/scanner/%s' % self.id,
            'target': 'fullscreen',
        }

    @api.depends('today_consumption_ids.ticket_count')
    def _compute_today_totals(self):
        for game in self:
            game.today_total_tickets = sum(game.today_consumption_ids.mapped('ticket_count'))

    @api.depends('ticket_line_ids.quantity', 'ticket_line_ids.amount')
    def _compute_bulk_totals(self):
        for game in self:
            game.total_bulk_quantity = sum(game.ticket_line_ids.mapped('quantity'))
            game.total_bulk_amount = sum(game.ticket_line_ids.mapped('amount'))

    def action_pay_investor(self):
        """Create a vendor bill for the investor from the bulk ticket lines."""
        self.ensure_one()
        if not self.investor_id:
            raise UserError(_('Please set an Investor on this game before paying.'))
        if not self.ticket_line_ids:
            raise UserError(_('Please add at least one ticket line in the "Bulk ticket entry" tab.'))

        Journal = self.env['account.journal']
        journal = Journal.search([
            ('company_id', '=', self.company_id.id),
            ('type', '=', 'purchase'),
        ], limit=1)
        if not journal:
            raise UserError(_('No purchase journal found for company %s.', self.company_id.name))

        invoice_lines = []
        for line in self.ticket_line_ids:
            account = line.product_id.property_account_expense_id or line.product_id.categ_id.property_account_expense_categ_id
            if not account:
                raise UserError(_('Product %s has no expense account configured.', line.product_id.display_name))
            invoice_lines.append((0, 0, {
                'display_type': 'product',
                'product_id': line.product_id.id,
                'name': line.product_id.display_name,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'account_id': account.id,
                'product_uom_id': line.product_id.uom_id.id,
            }))

        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.investor_id.id,
            'game_id': self.id,
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

    def action_open_investor_bills(self):
        """Open the list of vendor bills (investor payments) for this game."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Investor bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('game_id', '=', self.id), ('move_type', '=', 'in_invoice')],
            'context': {'default_move_type': 'in_invoice', 'default_partner_id': self.investor_id.id, 'default_game_id': self.id},
        }
