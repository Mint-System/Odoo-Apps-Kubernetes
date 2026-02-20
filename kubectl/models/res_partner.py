# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = ["res.partner"]

    cluster_ids = fields.One2many("kubectl.cluster", "partner_id", string="Clusters")
