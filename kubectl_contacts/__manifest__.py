# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Kubectl Contacts",
    "summary": """
        Contacts filter for provider and consulting partners.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "contacts", "kubectl"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
