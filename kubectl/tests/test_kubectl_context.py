import logging
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestKubectlContext(TransactionCase):
    """
    Tests for kubectl.context model.
    """

    def setUp(self):
        super().setUp()

        self.provider = self.env["res.partner"].create(
            {
                "name": "localhost",
            }
        )

        self.cluster = self.env["kubectl.cluster"].create(
            {
                "name": "Kind",
                "alias": "loc",
                "server": "https://host.docker.internal:35249",
                "domain": "knd.local",
                "partner_id": self.provider.id,
            }
        )

        self.context = self.env["kubectl.context"].create(
            {
                "name": "Admin",
                "cluster_id": self.cluster.id,
            }
        )

    def test_connection_to_kind_cluster(self):
        """
        Test connection to the kind cluster.
        """
        # Mock the run method to avoid actual kubectl execution
        mock_result = MagicMock()
        mock_result.stdout = "Kubernetes control plane is running at https://host.docker.internal:35249"
        mock_result.stderr = ""
        mock_result.returncode = 0

        # Mock the run method at the class level instead of instance level
        with patch.object(type(self.context), "run", return_value=mock_result) as mock_run:
            result = self.context.action_test_connection()

            # Verify that run was called with the correct command
            mock_run.assert_called_once_with(["kubectl", "cluster-info"])

            # Verify the result structure
            self.assertEqual(result["type"], "ir.actions.client")
            self.assertEqual(result["tag"], "display_notification")
            self.assertEqual(result["params"]["title"], "Connection Success")
            self.assertEqual(result["params"]["type"], "success")
            self.assertEqual(result["params"]["message"], mock_result.stdout)
