# -*- coding: utf-8 -*-
{
    'name': 'Yadouda Game Tickets Scanner',
    'version': '1.0',
    'category': 'Operations',
    'summary': 'Scan and record game ticket consumption for park games',
    'description': """
Yadouda Game Tickets Scanner
============================
* Manage park games and assign operators
* Full-screen scanner interface for barcode tickets
* Record ticket consumption per game and date
* Operator and manager security groups
    """,
    'author': 'HACHEMI Mohamed Ramzi',
    'email': 'mohamed.ramzi.hachemi@gmail.com',
    'website': 'https://www.linkedin.com/in/mohamed-djazairi-574b4a15b/',
    'depends': ['base', 'web'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/game_views.xml',
        'views/ticket_consumption_views.xml',
        'views/menu_views.xml',
        'templates/scanner_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
