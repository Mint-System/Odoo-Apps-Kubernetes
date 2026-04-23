import json
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class KubectlNamespace(models.Model):
    _inherit = "kubectl.namespace"

    @api.model
    def _import_namespaces(self, context_id):
        """
        Kubernetes API wrapper.
        Load all namespaces from the current context.
        Creat missing namespace entries.
        """
        cluster_id = context_id.cluster_id
        command = f"kubectl get {self._kubernetes_resource} -o json".split(" ")
        result = context_id.run(command)
        data = json.loads(result.stdout)
        for item in data["items"]:
            name = item["metadata"]["name"]
            uid = item["metadata"]["uid"]
            namespace_id = self.search([("name", "=", name), ("cluster_id", "=", cluster_id.id)])
            if namespace_id:
                namespace_id.write({"uid": uid})
            else:
                self.create({"name": name, "uid": uid, "cluster_id": cluster_id.id})
        return len(data["items"])
