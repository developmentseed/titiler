## k8s / Helm Deployment

Try locally

```
minikube start
kubectl config use-context minikube
helm init --wait

# in the k8s directory
helm install -f titiler/Chart.yaml titiler
```

For more info about K8S cluster and node configuration please see: https://github.com/developmentseed/titiler/issues/212
