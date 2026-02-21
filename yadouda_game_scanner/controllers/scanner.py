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

        # Required by website's frontend_layout inheritance (avoids KeyError: 'website')
        qcontext = {
            'game': game,
            'main_object': game,
        }
        if hasattr(request, 'website') and request.website:
            qcontext['website'] = request.website
        elif 'website' in request.env:
            qcontext['website'] = request.env['website'].get_current_website()
        return request.render('yadouda_game_scanner.scanner_template', qcontext)

    @http.route('/yadouda/scan', auth='user', type='json')
    def scan_ticket(self, game_id, ticket_code):
        return request.env['ticket.consumption'].scan_ticket(game_id, ticket_code)
