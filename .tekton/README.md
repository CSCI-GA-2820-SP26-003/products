# Tekton CD resources

## Pipelines

- `products-cd-pipeline` ([`pipeline.yaml`](pipeline.yaml)) — clone, lint, test, build (buildah), deploy (`deploy-image` task).

## Deploy task (`deploy-image`)

The deploy step:

1. Applies `k8s/deployment.yaml` and `k8s/service.yaml` from the cloned repo.
2. Sets the running image with `oc set image` to match the `IMAGE_NAME` built in the previous stage.
3. Verifies rollout with `oc rollout status` (fails the task on failure).

### Service account / RBAC

The `PipelineRun` must use a ServiceAccount (e.g. `pipeline`) whose role allows at least:

- `get`, `list`, `watch`, `patch`, `update`, `create` on `deployments` / `deployments/scale`
- `get`, `list`, `watch` on `pods`, `replicasets`
- `get`, `watch` on events (optional, for debugging)

If `oc rollout status` or `oc set image` returns `Forbidden`, ask your cluster admin to grant the above to the pipeline SA in the target namespace.

## Webhook / TriggerTemplate

[`events/trigger_template.yaml`](events/trigger_template.yaml) creates a `PipelineRun` that references **`products-cd-pipeline`**, binds workspace **`products-pipeline-workspace`** to PersistentVolumeClaim **`pipeline-pvc`** ([`workspace.yaml`](workspace.yaml)), and passes **`GIT_REPO`**, **`GIT_REF`** (push commit SHA), and **`IMAGE_NAME`** to match [`pipeline.yaml`](pipeline.yaml).
