# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class BdeUpdateTemplate(models.Model):
    _name = 'bde.update.template'
    _description = 'Bulk Update Template'
    _order = 'last_used desc'

    name = fields.Char(string='Template Name', required=True)
    model_name = fields.Char(string='Target Model', required=True)
    description = fields.Text(string='Description')
    line_ids = fields.One2many('bde.update.line', 'template_id', string='Update Lines')
    is_active = fields.Boolean(string='Active', default=True)
    last_used = fields.Datetime(string='Last Used', readonly=True)
    times_used = fields.Integer(string='Times Used', default=0, readonly=True)

    def action_apply_template(self):
        """Create a new update job from this template."""
        for template in self:
            job = self.env['bde.update.job'].create({
                'name': _('Job from template: %s') % template.name,
                'model_name': template.model_name,
                'update_mode': 'set',
            })
            for line in template.line_ids:
                self.env['bde.update.line'].create({
                    'job_id': job.id,
                    'field_name': line.field_name,
                    'operation': line.operation,
                    'value': line.value,
                    'value_type': line.value_type,
                })
            template.last_used = fields.Datetime.now()
            template.times_used += 1
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'bde.update.job',
                'res_id': job.id,
                'view_mode': 'form',
                'target': 'current',
            }
