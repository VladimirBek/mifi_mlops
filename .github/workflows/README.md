# CI/CD Workflows

## Required GitHub Secrets
- GHCR_USERNAME: GitHub username or org name that owns the GHCR packages
- GHCR_TOKEN: GitHub PAT with `read:packages` and `write:packages`
- KUBECONFIG_STAGING_B64: base64-encoded kubeconfig for staging cluster
- KUBECONFIG_PRODUCTION_B64: base64-encoded kubeconfig for production cluster

Optional (for external monitor checks):
- STAGING_HOST: public host used by Ingress (e.g. staging.example.com)
- PRODUCTION_HOST: public host used by Ingress (e.g. api.example.com)

## Notes
- `Build and Test` runs lint+tests and executes `dvc repro --no-scm` to build the dataset/model locally.
- Deploy workflows apply k8s manifests and set images to the commit SHA tag.
- `Canary Release (Istio)` is optional and assumes Istio is installed in the cluster.
