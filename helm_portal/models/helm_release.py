from odoo import models


class HelmRelease(models.Model):
    _name = "helm.release"
    _inherit = ["helm.release", "portal.mixin"]

    def _compute_access_url(self):
        """Override portal.mixin method to set the correct portal URL"""
        super()._compute_access_url()
        for release in self:
            release.access_url = f"/my/release/{release.id}"
