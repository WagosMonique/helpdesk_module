# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.depends('start_time', 'end_time', 'break_time', 'break_unit_amount')#this api depends on if there is a change in any of these values
    def _get_unit_amount(self):
        for rec in self:
            unit_amount = 0
            if rec.start_time and (rec.break_time or rec.end_time):
                if rec.end_time:
                    unit_amount = rec.end_time - rec.start_time
                else:
                    unit_amount = rec.break_time - rec.start_time
                unit_amount = unit_amount.total_seconds() / 60 / 60
                if rec.break_unit_amount:
                    unit_amount -= rec.break_unit_amount
            rec.unit_amount = unit_amount

    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    break_time = fields.Datetime(
        string='Break Time',
        readonly=True,
        copy=False)
    break_unit_amount = fields.Float(string='Break Time (Hour(s))')
    unit_amount = fields.Float(compute='_get_unit_amount', store=True)

    def button_break(self):
        for rec in self.filtered(lambda t: t.start_time and not t.end_time and not t.break_time):
            rec.write({
                'break_time': fields.Datetime.now(),
            })

    def button_resume(self):
        for rec in self.filtered(lambda t: t.break_time):
            additional_break = fields.Datetime.now() - rec.break_time
            additional_break = additional_break.total_seconds() / 3600.0
            rec.write({
                'break_time': False,
                'break_unit_amount': rec.break_unit_amount + additional_break
            })

    @api.constrains('end_time')
    def _check_break_time(self):
        for rec in self:
            if rec.end_time and rec.break_time:
                raise ValidationError(_(f'Please click button resume first for timesheet {rec.display_name}.'))
