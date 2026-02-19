# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager

_logger = logging.getLogger(__name__)


class CustomerPortal(portal.CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        HelmRelease = request.env["helm.release"]
        if "release_count" in counters:
            count = (
                HelmRelease.search_count([("partner_id", "=", request.env.user.partner_id.id)])
                if HelmRelease.has_access("read")
                else 0
            )
            values["release_count"] = count
            # Debug: log the count
            _logger.info(f"Helm Portal: release_count computed as {count}")
        return values

    @http.route(["/my/releases", "/my/releases/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_releases(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        HelmRelease = request.env["helm.release"]

        domain = [("partner_id", "=", request.env.user.partner_id.id)]

        # count for pager
        count = HelmRelease.search_count(domain)

        # make pager
        pager = portal_pager(url="/my/releases", url_args={}, total=count, page=page, step=self._items_per_page)

        # search the releases to display, according to the pager data
        releases = HelmRelease.search(domain, order="name asc", limit=self._items_per_page, offset=pager["offset"])
        request.session["my_releases_history"] = releases.ids[:100]

        values.update(
            {
                "releases": releases,
                "page_name": "releases",
                "pager": pager,
                "default_url": "/my/releases",
            }
        )
        return request.render("helm_portal.portal_my_releases", values)

    @http.route(["/my/release/<int:release_id>"], type="http", auth="public", website=True)
    def portal_my_release(self, release_id=None, access_token=None, **kw):
        try:
            release_sudo = self._document_check_access("helm.release", release_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")

        # Handle update action
        if kw.get("update") == "True":
            # Update values from form
            for value in release_sudo.value_ids:
                form_value = kw.get(f"value_{value.id}")
                if form_value is not None:
                    value.value = form_value

            # Trigger upgrade action
            result = release_sudo.action_upgrade()

            # Refresh the release data
            release_sudo.refresh()

            # Add notification message
            values = self._get_page_view_values(release_sudo, access_token, {}, False, False, **kw)
            values["release"] = release_sudo
            values["notification"] = {
                "message": "Release updated successfully",
                "type": "success",
                "output": release_sudo.output or "",
            }
            return request.render("helm_portal.portal_my_release", values)

        values = self._get_page_view_values(release_sudo, access_token, {}, False, False, **kw)
        values["release"] = release_sudo
        return request.render("helm_portal.portal_my_release", values)
