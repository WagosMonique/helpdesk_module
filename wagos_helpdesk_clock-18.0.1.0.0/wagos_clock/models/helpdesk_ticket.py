# models/helpdesk_ticket.py
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    # Add timer-related fields to ticket
    current_timer_id = fields.Many2one('account.analytic.line', 'Current Running Timer')
    has_running_timer = fields.Boolean('Has Running Timer', compute='_compute_has_running_timer')
    total_logged_time = fields.Float('Total Logged Time', compute='_compute_total_logged_time')
    
    @api.depends('current_timer_id')
    def _compute_has_running_timer(self):
        for ticket in self:
            ticket.has_running_timer = bool(ticket.current_timer_id and ticket.current_timer_id.is_timer_running)
    
    @api.depends('timesheet_ids.unit_amount')
    def _compute_total_logged_time(self):
        for ticket in self:
            ticket.total_logged_time = sum(ticket.timesheet_ids.mapped('unit_amount'))
    
    def action_start_ticket_timer(self):
        """Start a new timer for this ticket"""
        # Check if user already has a running timer
        employee = self.env.user.employee_id
        if not employee:
            raise UserError("You must be linked to an employee to use the timer.")
        
        running_timers = self.env['account.analytic.line'].search([
            ('employee_id', '=', employee.id),
            ('is_timer_running', '=', True)
        ])
        
        if running_timers:
            raise UserError("You already have a running timer. Please stop it first.")
        
        # Create new timesheet entry with timer
        timesheet_vals = {
            'name': f'Work on {self.name}',
            'helpdesk_ticket_id': self.id,
            'project_id': self.project_id.id if self.project_id else False,
            'task_id': self.task_id.id if self.task_id else False,
            'employee_id': employee.id,
            'timer_start': fields.Datetime.now(),
            'is_timer_running': True,
            'unit_amount': 0,
        }
        
        new_timesheet = self.env['account.analytic.line'].create(timesheet_vals)
        self.current_timer_id = new_timesheet.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_stop_ticket_timer(self):
        """Stop the current timer for this ticket"""
        if not self.current_timer_id:
            raise UserError("No timer is running for this ticket.")
        
        self.current_timer_id.action_stop_timer()
        self.current_timer_id = False
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    # Timer fields
    timer_start = fields.Datetime('Timer Start')
    timer_stop = fields.Datetime('Timer Stop')
    is_timer_running = fields.Boolean('Timer Running', default=False)
    break_time = fields.Float('Break Time (Hours)', default=0.0)
    timer_duration = fields.Float('Timer Duration', compute='_compute_timer_duration')
    
    @api.depends('timer_start', 'timer_stop', 'is_timer_running')
    def _compute_timer_duration(self):
        for record in self:
            if record.timer_start:
                if record.is_timer_running:
                    # Timer is running, calculate current duration
                    duration = fields.Datetime.now() - record.timer_start
                    record.timer_duration = duration.total_seconds() / 3600
                elif record.timer_stop:
                    # Timer stopped, calculate final duration
                    duration = record.timer_stop - record.timer_start
                    record.timer_duration = duration.total_seconds() / 3600
                else:
                    record.timer_duration = 0.0
            else:
                record.timer_duration = 0.0
    
    def action_start_timer(self):
        """Start timer for this timesheet entry"""
        if self.is_timer_running:
            raise UserError("Timer is already running!")
        
        # Check for other running timers
        employee = self.env.user.employee_id
        running_timers = self.search([
            ('employee_id', '=', employee.id),
            ('is_timer_running', '=', True),
            ('id', '!=', self.id)
        ])
        
        if running_timers:
            raise UserError("You have another timer running. Please stop it first.")
        
        self.write({
            'timer_start': fields.Datetime.now(),
            'is_timer_running': True,
        })
        
        # Update ticket's current timer
        if self.helpdesk_ticket_id:
            self.helpdesk_ticket_id.current_timer_id = self.id
    
    def action_stop_timer(self):
        """Stop timer and update duration"""
        if not self.is_timer_running:
            raise UserError("No timer is running!")
        
        stop_time = fields.Datetime.now()
        if self.timer_start:
            duration = stop_time - self.timer_start
            hours = duration.total_seconds() / 3600 - self.break_time
            
            self.write({
                'timer_stop': stop_time,
                'is_timer_running': False,
                'unit_amount': max(hours, 0),  # Ensure non-negative
            })
            
            # Clear ticket's current timer
            if self.helpdesk_ticket_id and self.helpdesk_ticket_id.current_timer_id == self:
                self.helpdesk_ticket_id.current_timer_id = False