# Tekton CD resources

## Pipelines

- `products-cd-pipeline` (`pipeline.yaml`) — clone, lint, test, build (buildah), deploy (`deploy-image` task).

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

## Webhook / trigger alignment (deferred)

[`.tekton/events/trigger_template.yaml`](events/trigger_template.yaml) references `pipelineRef.name: cd-pipeline` and workspace `pipeline-workspace`, while this repo’s Pipeline is named `products-cd-pipeline` and uses `products-pipeline-workspace`. Until those are aligned (and the PVC name matches), webhook-created `PipelineRuns` may fail to resolve the pipeline or bind workspaces. Manual `tkn pipeline start` works when parameters and workspaces are supplied explicitly.
