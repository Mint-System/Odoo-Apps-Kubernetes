{
    "name": "Helm Mint Cloud",
    "summary": """
        Mint Cloud helm data.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["helm", "kubectl_mintcloud"],
    "data": ["data/data.xml", "data/helm_chart_odoo_data.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "external_dependencies": {"bin": ["helm"]},
}
