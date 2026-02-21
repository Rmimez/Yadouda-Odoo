# -*- coding: utf-8 -*-

from odoo import models, fields, api


class YadoudaGame(models.Model):
    _name = 'yadouda.game'
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

    # Current consumption tracking
    today_consumption_ids = fields.One2many(
        'ticket.consumption',
        'game_id',
        domain=[('date', '=', fields.Date.today)]
    )
    today_total_tickets = fields.Integer(
        string="Today's Tickets",
        compute='_compute_today_totals'
    )

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
