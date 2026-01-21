{
    "name": "Website Kubectl",
    "summary": """
        Present Kuberentes clusters on website.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["website", "kubectl"],
    "data": ["views/kubectl_cluster_views.xml", "views/website_kubectl_cluster_templates.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
