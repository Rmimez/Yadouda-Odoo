# -*- coding: utf-8 -*-

from odoo import models, fields, api


class YadoudaGame(models.Model):
    _name = 'yadouda.game'
    _inherit = ['image.mixin']
    _description = 'Park Game'
    _rec_name = 'name'

    name = fields.Char(string='Game Name', required=True)
    code = fields.Char(string='Game Code', required=True, help='Short code for scanning')
    active = fields.Boolean(string='Active', default=True)

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
