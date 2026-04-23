import logging
import subprocess

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class KubernetesResource(models.AbstractModel):
    _name = "kubernetes.resource"
    _description = "Kubernetes Resource Mixin"

    name = fields.Char(required=True)
    uid = fields.Char(readonly=True, help="Kuberentes resource identifier.")

    def action_get_uid(self):
        """
        Kubernetes API wrapper.
        Fetch Kubernetes uid for a given name from cluster.
        """
        for resource in self:
            # Check if resource is connected to release or cluster and load context
            context_id = False
            if hasattr(resource, "release_id"):
                context_id = resource.release_id.cluster_id.context_id
            if hasattr(resource, "cluster_id"):
                context_id = resource.cluster_id.context_id

            if not context_id:
                raise UserError(_("'context_id' not found in Kuberentes resource %s.") % resource.name)

            try:
                cmd = ["kubectl", "get", resource._kubernetes_resource, resource.name, "-o", "jsonpath={.metadata.uid}"]
                result = context_id.run(cmd)
                uid = result.stdout.strip()
                if uid:
                    resource.uid = uid
                else:
                    resource.uid = False
            except subprocess.CalledProcessError as e:
                resource.uid = False
                _logger.warning(f"Failed to get UID for {resource.name}: {e.stderr}")
