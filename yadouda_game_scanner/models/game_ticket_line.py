# -*- coding: utf-8 -*-

from odoo import models, fields, api


class YadoudaGameTicketLine(models.Model):
    _name = 'yadouda.game.ticket.line'
    _description = 'Game ticket line (bulk entry)'
    _order = 'date desc, id desc'

    game_id = fields.Many2one('yadouda.game', string='Game', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    product_id = fields.Many2one(
        'product.product',
        string='Ticket / Product',
        domain=[('sale_ok', '=', True)],
        required=True,
    )
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_price = fields.Float(string='Unit Price', digits='Product Price', default=0.0)
    amount = fields.Float(string='Total', compute='_compute_amount', store=True, digits='Product Price')
    currency_id = fields.Many2one(
        'res.currency',
        related='game_id.currency_id',
        readonly=True,
    )

    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.list_price
