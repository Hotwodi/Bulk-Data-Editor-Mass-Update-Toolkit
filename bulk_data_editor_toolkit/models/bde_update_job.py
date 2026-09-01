# -*- coding: utf-8 -*-
import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BdeUpdateJob(models.Model):
    _name = 'bde.update.job'
    _description = 'Bulk Update Job'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'created_date desc'

    name = fields.Char(string='Job Name', required=True, tracking=True)
    model_name = fields.Char(string='Target Model', required=True, tracking=True,
                             help='Technical name of the model to update (e.g. res.partner).')
    domain_filter = fields.Text(string='Domain Filter',
                                help='JSON-encoded domain list to filter records, e.g. [["active","=",true]].')
    update_mode = fields.Selection(
        selection=[
            ('set', 'Set'),
            ('append', 'Append'),
            ('replace', 'Replace'),
            ('clear', 'Clear'),
            ('formula', 'Formula'),
        ],
        string='Update Mode',
        default='set',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('running', 'Running'),
            ('done', 'Done'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    records_affected = fields.Integer(string='Records Affected', readonly=True, copy=False)
    line_ids = fields.One2many('bde.update.line', 'job_id', string='Update Lines')
    undo_log_ids = fields.One2many('bde.undo.log', 'job_id', string='Undo Logs')
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now, readonly=True)
    note = fields.Html(string='Notes')

    def _eval_domain(self):
        """Parse and evaluate the domain filter text into a valid domain list."""
        self.ensure_one()
        if not self.domain_filter:
            return []
        try:
            domain = json.loads(self.domain_filter)
        except (ValueError, TypeError) as exc:
            raise UserError(_('Invalid domain filter JSON: %s') % exc)
        if not isinstance(domain, list):
            raise UserError(_('Domain filter must be a JSON list of tuples/lists.'))
        return domain

    def _get_target_model(self):
        """Return the model object for the configured model_name."""
        self.ensure_one()
        if self.model_name not in self.env:
            raise UserError(_('Model "%s" does not exist.') % self.model_name)
        return self.env[self.model_name]

    def action_run(self):
        """Execute the bulk update job."""
        for job in self:
            if job.state == 'running':
                continue
            job.state = 'running'
            target_model = job._get_target_model()
            domain = job._eval_domain()
            records = target_model.search(domain)
            undo_logs = self.env['bde.undo.log']
            for record in records:
                record_data = {}
                for line in job.line_ids:
                    if line.field_name not in record._fields:
                        continue
                    record_data[line.field_name] = record[line.field_name]
                if record_data:
                    undo_logs |= self.env['bde.undo.log'].create({
                        'name': _('Undo: %s [%s]') % (job.name, record.display_name),
                        'job_id': job.id,
                        'model_name': job.model_name,
                        'record_id': record.id,
                        'record_data': json.dumps(record_data, default=str),
                        'can_restore': True,
                    })
                for line in job.line_ids:
                    line._apply(record)
            job.records_affected = len(records)
            job.state = 'done'
        return True

    def action_reset_draft(self):
        for job in self:
            job.state = 'draft'
            job.records_affected = 0
        return True

    def action_undo(self):
        """Undo all changes made by this job using the undo logs."""
        for job in self:
            for log in job.undo_log_ids.filtered('can_restore'):
                log.action_restore()
        return True
