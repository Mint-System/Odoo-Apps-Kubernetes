# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestHelmRelease(TransactionCase):
    def test_value_eval(self):
        """
        Test that helm values are evaluated correctly using existing Odoo chart from data.xml.
        """
        odoo_chart = self.env.ref("helm.chart_odoo")
        cluster = self.env.ref("kubectl.kubectl_cluster_kind_demo")

        # Create a release using the Odoo chart
        release = self.env["helm.release"].create(
            {"name": "test-odoo-release", "chart_id": odoo_chart.id, "cluster_id": cluster.id, "state": "draft"}
        )

        # Trigger computation of values
        release._compute_values()

        # Check that values contain the expected fields
        self.assertIn("init:", release.values)
        self.assertIn("password:", release.values)

    def test_product_filter_value(self):
        """
        Test that helm chart values with product filters are applied correctly.
        """
        # Get references
        odoo_chart = self.env.ref("helm.chart_odoo")
        enterprise_product = self.env.ref("helm.product_odoo_enterprise_edition")
        community_product = self.env.ref("helm.product_odoo_community_edition")
        cluster = self.env.ref("kubectl.kubectl_cluster_kind_demo")

        # Create releases for both products
        enterprise_release = self.env["helm.release"].create(
            {"name": "test-enterprise-release", "chart_id": odoo_chart.id, "cluster_id": cluster.id, "state": "draft"}
        )

        community_release = self.env["helm.release"].create(
            {"name": "test-community-release", "chart_id": odoo_chart.id, "cluster_id": cluster.id, "state": "draft"}
        )

        # Test the downloadOdooEnterprise value which should only apply to enterprise edition
        download_enterprise_value = self.env.ref("helm.chart_odoo_value_download_enterprise")

        # Check that the value has the correct product filter
        self.assertTrue(download_enterprise_value.filter_product_ids)
        self.assertEqual(len(download_enterprise_value.filter_product_ids), 1)
        self.assertEqual(download_enterprise_value.filter_product_ids[0], enterprise_product.product_tmpl_id)

        # Check that the value's path is correct
        self.assertEqual(download_enterprise_value.path, "downloadOdooEnterprise")
        self.assertEqual(download_enterprise_value.value, "true")
