# __manifest__.py
{
    'name': 'Helpdesk Timesheet Timer',
    'version': '18.0.1.0.0',
    'summary': 'Add start/stop timer functionality to helpdesk timesheet',
    'description': '''
        This module adds timer functionality to helpdesk tickets:
        - Start/Stop timer buttons on ticket form
        - Timer controls in timesheet tab
        - Track actual time spent on tickets
        - Prevent multiple running timers
        - Visual indicators for running timers
    ''',
    'author': 'Wagos.Ltd',
    'website': 'https://wagos.com',
    'category': 'Helpdesk',
    'depends': [
        'base',
        'helpdesk',
        'helpdesk_timesheet',
        'hr_timesheet',
    ],
    'data': [
        'views/helpdesk_timer_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}