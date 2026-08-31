# -*- coding: utf-8 -*-
{
    'name': 'Bulk Data Editor & Mass Update Toolkit',
    'version': '18.0.1.0.0',
    'category': 'Productivity/AI',
    'summary': 'Bulk update, mass edit, and undo changes on any Odoo model safely.',
    'description': """
Bulk Data Editor & Mass Update Toolkit
======================================

Safely perform bulk updates and mass edits on any Odoo model with full
undo support, reusable templates, and multiple operation modes (set,
append, replace, clear, increment, multiply and formula).

Features:
- Bulk update jobs with domain filters
- Multiple update modes: set, append, replace, clear, formula
- Per-field operations: set, append, replace, clear, increment, multiply
- Reusable update templates
- Full undo log with restore capability
""",
    'author': 'SoftaiDev',
    'website': 'https://softaidev.pages.dev',
    'license': 'LGPL-3',
    'price': 29.99,
    'currency': 'USD',
    'application': True,
    'installable': True,
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/bde_update_job_views.xml',
        'views/bde_update_line_views.xml',
        'views/bde_update_template_views.xml',
        'views/bde_undo_log_views.xml',
        'views/menu.xml',
    ],
}
