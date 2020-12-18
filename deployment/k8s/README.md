## k8s / Helm Deployment

Try locally

```
minikube start
kubectl config use-context minikube
helm init --wait

# in the k8s directory
helm install -f titiler/Chart.yaml titiler
```
