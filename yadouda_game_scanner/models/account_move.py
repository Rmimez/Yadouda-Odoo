# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    game_id = fields.Many2one(
        'yadouda.game',
        string='Game',
        copy=False,
        index=True,
    )
