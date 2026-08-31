# -*- coding: utf-8 -*-
import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BdeUndoLog(models.Model):
    _name = 'bde.undo.log'
    _description = 'Undo Log'
    _order = 'undone_date desc, id desc'

    name = fields.Char(string='Name', required=True)
    job_id = fields.Many2one('bde.update.job', string='Job', ondelete='cascade')
    model_name = fields.Char(string='Model', required=True)
    record_id = fields.Integer(string='Record ID', required=True)
    record_data = fields.Text(string='Record Data', required=True,
                              help='JSON-encoded snapshot of field values before the update.')
    undone_by = fields.Many2one('res.users', string='Undone By', readonly=True)
    undone_date = fields.Datetime(string='Undone Date', readonly=True)
    can_restore = fields.Boolean(string='Can Restore', default=True)

    def action_restore(self):
        """Restore the record to its pre-update state."""
        for log in self:
            if not log.can_restore:
                raise UserError(_('This undo log has already been restored.'))
            if log.model_name not in self.env:
                raise UserError(_('Model "%s" no longer exists.') % log.model_name)
            record = self.env[log.model_name].browse(log.record_id)
            if not record.exists():
                raise UserError(_('Record %s of %s no longer exists.') % (log.record_id, log.model_name))
            try:
                data = json.loads(log.record_data)
            except (ValueError, TypeError) as exc:
                raise UserError(_('Invalid record data JSON: %s') % exc)
            for field_name, value in data.items():
                if field_name in record._fields:
                    record[field_name] = value
            log.can_restore = False
            log.undone_by = self.env.user.id
            log.undone_date = fields.Datetime.now()
        return True
