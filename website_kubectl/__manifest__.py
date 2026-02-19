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
    "depends": ["website", "kubectl", "website_partner"],
    "data": [
        "data/website_kubectl_data.xml",
        "views/kubectl_cluster_views.xml",
        "views/website_kubectl_cluster_templates.xml",
    ],
    "demo": ["demo/website_kubectl_demo.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
