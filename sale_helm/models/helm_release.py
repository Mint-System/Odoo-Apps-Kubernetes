import logging

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class HelmRelease(models.Model):
    _inherit = "helm.release"

    sale_line_id = fields.Many2one("sale.order.line", string="Sale Order Line")

    def _eval_value(self, expression):
        """
        Add order_id to context.
        """
        order_id = self.sale_line_id.order_id if self.sale_line_id else False
        context = {
            "self": self,
            "release": self,
            "release_id": self,
            "generate_password": self.generate_password,
            "order": order_id,
            "order_id": order_id,
        }
        try:
            return safe_eval(expression, context)
        except:
            return False

    def action_install(self):
        """
        Override the install action to send email notification when release is installed.
        """
        # Call the original method first
        result = super().action_install()

        # Send email notification if release is linked to a sale order line
        for release in self:
            if release.sale_line_id and release.state == "installed":
                try:
                    mail_template = self.env.ref("sale_helm.email_template_sale_order_helm_release")
                    # Send email in the context of the sale order
                    release.sale_line_id.order_id.with_context(force_send=True).message_post_with_source(
                        mail_template,
                        message_type="comment",
                        email_layout_xmlid="mail.mail_notification_light",
                    )
                except Exception as e:
                    _logger.error(f"Failed to send release notification email: {str(e)}")

        return result
