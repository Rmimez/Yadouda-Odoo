# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TicketConsumption(models.Model):
    _name = 'ticket.consumption'
    _description = 'Game Ticket Consumption'
    _order = 'date desc, create_date desc'

    game_id = fields.Many2one('yadouda.game', string='Game', required=True)
    operator_id = fields.Many2one(
        'res.users',
        string='Operator',
        default=lambda self: self.env.user,
        required=True
    )
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    # Optional: add sale_order_id and depend on 'sale' if you use Sale orders
    # sale_order_id = fields.Many2one('sale.order', string='Daily Sale Order')

    # Ticket details
    ticket_code = fields.Char(string='Ticket Barcode', required=True)
    ticket_count = fields.Integer(string='Number of Tickets', default=1)

    # Links to existing systems
    notes = fields.Text(string='Notes')

    # Validation
    @api.constrains('operator_id', 'game_id')
    def _check_operator_access(self):
        for record in self:
            if record.operator_id not in record.game_id.responsible_user_ids:
                raise models.ValidationError(
                    'Operator is not authorized for this game!'
                )

    # Scanner method
    @api.model
    def scan_ticket(self, game_id, ticket_code):
        """Method called by scanner interface"""
        game = self.env['yadouda.game'].browse(game_id)

        # Check if current user is authorized
        if self.env.user not in game.responsible_user_ids:
            return {
                'status': 'error',
                'message': 'You are not authorized for this game'
            }

        # Create consumption record
        self.create({
            'game_id': game_id,
            'ticket_code': ticket_code,
            'operator_id': self.env.user.id,
        })

        # Invalidate computed fields so next read returns updated totals
        game.invalidate_recordset(['today_consumption_ids', 'today_total_tickets'])
        return {
            'status': 'success',
            'message': f'Ticket {ticket_code} recorded',
            'game_total': game.today_total_tickets
        }
