# Sample Workloads

These workloads intentionally create Kubernetes failure modes for KubeSight AI to
detect during local demos.

## Included Signals

- `payment-service`: exits on startup to trigger `CrashLoopBackOff`.
- `orders-service`: exceeds a small memory limit to trigger `OOMKilled`.
- `inventory-service`: references a missing image to trigger `ImagePullBackOff`.
- `checkout-service`: stays running and emits timeout and database errors.
- `report-worker`: burns CPU within a small CPU limit.

## Apply

```bash
kubectl apply -k kubernetes/sample-apps
kubectl get pods -n kubesight-samples -w
```

After the pods settle, open KubeSight AI and inspect the `kubesight-samples`
namespace.

## Remove

```bash
kubectl delete -k kubernetes/sample-apps
```
