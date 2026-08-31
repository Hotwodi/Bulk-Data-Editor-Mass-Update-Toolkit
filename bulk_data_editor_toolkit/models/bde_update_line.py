# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BdeUpdateLine(models.Model):
    _name = 'bde.update.line'
    _description = 'Bulk Update Line'

    job_id = fields.Many2one('bde.update.job', string='Job', ondelete='cascade')
    template_id = fields.Many2one('bde.update.template', string='Template', ondelete='cascade')
    field_name = fields.Char(string='Field Name', required=True,
                             help='Technical name of the field to update.')
    operation = fields.Selection(
        selection=[
            ('set', 'Set'),
            ('append', 'Append'),
            ('replace', 'Replace'),
            ('clear', 'Clear'),
            ('increment', 'Increment'),
            ('multiply', 'Multiply'),
        ],
        string='Operation',
        default='set',
        required=True,
    )
    value = fields.Text(string='Value', help='The value to apply. For reference fields use "model,id".')
    value_type = fields.Selection(
        selection=[
            ('text', 'Text'),
            ('number', 'Number'),
            ('boolean', 'Boolean'),
            ('date', 'Date'),
            ('reference', 'Reference'),
        ],
        string='Value Type',
        default='text',
        required=True,
    )

    def _coerce_value(self, record):
        """Convert the text value into the proper Python type for the target field."""
        self.ensure_one()
        field = record._fields.get(self.field_name)
        if not field:
            raise UserError(_('Field "%s" does not exist on model %s.') % (self.field_name, record._name))
        raw = (self.value or '').strip()
        if self.operation == 'clear':
            return False
        if self.value_type == 'boolean':
            return raw.lower() in ('true', '1', 'yes', 't')
        if self.value_type == 'number':
            try:
                return float(raw)
            except ValueError:
                raise UserError(_('Value "%s" is not a valid number.') % raw)
        if self.value_type == 'date':
            return fields.Date.to_date(raw)
        if self.value_type == 'reference':
            parts = raw.split(',')
            if len(parts) != 2:
                raise UserError(_('Reference value must be "model,id", got "%s".') % raw)
            ref_model = parts[0].strip()
            ref_id = int(parts[1].strip())
            return self.env[ref_model].browse(ref_id)
        return raw

    def _apply(self, record):
        """Apply this line's operation to a single record."""
        self.ensure_one()
        if not self.field_name or self.field_name not in record._fields:
            return
        if self.operation == 'clear':
            record[self.field_name] = False
            return
        value = self._coerce_value(record)
        if self.operation == 'set':
            record[self.field_name] = value
        elif self.operation == 'append':
            current = record[self.field_name]
            if isinstance(current, str):
                record[self.field_name] = (current or '') + str(value)
            elif isinstance(current, (int, float)):
                record[self.field_name] = current + value
            else:
                record[self.field_name] = value
        elif self.operation == 'replace':
            current = record[self.field_name]
            if isinstance(current, str) and isinstance(value, str):
                old_val = (self.value or '').split('|')[0].strip() if '|' in (self.value or '') else ''
                new_val = (self.value or '').split('|')[1].strip() if '|' in (self.value or '') else str(value)
                record[self.field_name] = (current or '').replace(old_val, new_val)
            else:
                record[self.field_name] = value
        elif self.operation == 'increment':
            current = record[self.field_name] or 0
            record[self.field_name] = current + value
        elif self.operation == 'multiply':
            current = record[self.field_name] or 0
            record[self.field_name] = current * value
        return True
