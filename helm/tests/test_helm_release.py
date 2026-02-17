# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestHelmRelease(TransactionCase):
    def test_value_eval(self):
        """
        Test that helm values are evaluated correctly using existing Odoo chart from data.xml.
        """
        odoo_chart = self.env.ref("helm.chart_odoo")
        cluster = self.env.ref("helm.ingress_nginx")

        # Create a release using the Odoo chart
        release = self.env["helm.release"].create(
            {"name": "test-odoo-release", "chart_id": odoo_chart.id, "cluster_id": cluster.id, "state": "draft"}
        )

        # Trigger computation of values
        release._compute_values()

        # Check that values contain the expected fields
        self.assertIn("init:", release.values)
        self.assertIn("password:", release.values)
