# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class YadoudaScanner(http.Controller):

    @http.route('/yadouda/scanner/<int:game_id>', auth='user', type='http')
    def scanner_interface(self, game_id):
        game = request.env['yadouda.game'].browse(game_id)

        # Check authorization
        if request.env.user not in game.responsible_user_ids:
            return request.render('web.http_error', {'status_code': 403, 'status_message': 'Not authorized'})

        return request.render('yadouda_game_scanner.scanner_template', {
            'game': game
        })

    @http.route('/yadouda/scan', auth='user', type='json')
    def scan_ticket(self, game_id, ticket_code):
        return request.env['ticket.consumption'].scan_ticket(game_id, ticket_code)
