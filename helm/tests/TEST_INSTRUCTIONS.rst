Prepare Kubernetes:

- Start local kind cluster
- Ensure the "kubernetes-build", "ingress-nginx" and "cnpg" repos are added
- Ensure local hostnames are set: cloud.local, odoo.cloud.local, restic.local and restic.cloud.local

Install ingress-nginx chart

- Open "Helm > Charts > ingress-nginx" and click "Release"
- Enter name "ingress-nginx" and select "Kind (loc)" as cluster
- Create namespace "ingress-nginx"
- Select customer "Mint System"
- Confirm and install release
- Refresh page and check if it was installed

Install cloudnative-pg chart

- Open "Helm > Charts > cloudnative-pg" and click "Release"
- Enter name "cloudnative-pg" and select "Kind (loc)" as cluster
- Create namespace "cnpg-system"
- Select customer "Mint System"
- Confirm and install release
- Refresh page and check if it was installed

Install odoo chart

- Open "Helm > Charts > odoo" and click "Release"
- Enter name "odoo" and select "Kind (loc)" as cluster
- Create namespace "odoo"
- Select customer "Mint System"
- Confirm and install release
- Refresh page and check if it was installed

Uninstall charts

- Open "Helm > Releases > odoo" and click "Uninstall"
- Open "ingress-nginx" release and click "Uninstall"
- Open "cloudnative-pg" release and click "Uninstall"
