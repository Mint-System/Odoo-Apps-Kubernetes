from odoo import http
from odoo.http import request


class WebsiteKubectlClusterPage(http.Controller):
    # Do not use semantic controller due to SUPERUSER_ID
    @http.route(["/clusters/<cluster_id>"], type="http", auth="public", website=True)
    def cluster_detail(self, cluster_id, **post):
        current_slug = cluster_id
        _, cluster_id = request.env["ir.http"]._unslug(cluster_id)
        if cluster_id:
            cluster_sudo = request.env["kubectl.cluster"].sudo().browse(cluster_id)
            is_website_restricted_editor = request.env.user.has_group("website.group_website_restricted_editor")
            if cluster_sudo.exists() and (cluster_sudo.website_published or is_website_restricted_editor):
                cluster_slug = request.env["ir.http"]._slug(cluster_sudo)
                if cluster_slug != current_slug:
                    return request.redirect("/clusters/%s" % cluster_slug)
                values = {
                    # See REVIEW_CAN_PUBLISH_UNSUDO
                    "main_object": cluster_sudo.with_context(can_publish_unsudo_main_object=True),
                    "cluster": cluster_sudo,
                    "edit_page": False,
                }
                return request.render("website_kubectl.cluster_page", values)
        raise request.not_found()
