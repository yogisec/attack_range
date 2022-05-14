#!/bin/bash

export KOPS_STATE_STORE=s3://kops-yogi-state-store/yogi.dev.us-east-1.k8s.local

# kops create cluster --zones=us-east-1f yogi.dev.us-east-1.k8s.local --node-count=2 --admin-access=70.179.208.28/32 --state s3://kops-yogi-state-store
# kops create -f yogi-init.yaml

# Install KOPS
curl -Lo kops https://github.com/kubernetes/kops/releases/download/$(curl -s https://api.github.com/repos/kubernetes/kops/releases/latest | grep tag_name | cut -d '"' -f 4)/kops-linux-amd64
chmod +x kops
sudo mv kops /usr/local/bin/kops



echo 'Setting up the cluster'
kops replace -f yogi-init.yaml --force
kops update cluster --name yogi.dev.us-east-1.k8s.local --yes --admin

echo 'Cluster Initialized, waiting for 5 minutes for everything to come online'

# Sleep for 5 minutes to let the cluster setup process complete
# We could do this more smarter less not smart, but this works and I don't have to think
sleep 5m

echo 'Installing cert manager CRDs'
# Install the custom resource definitions (CRD) for cert-manager to work
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.6.1/cert-manager.yaml
sleep 5
echo 'Installing Istio'
# Istio is pinned here to 1.13.3
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.13.3 TARGET_ARCH=x86_64 sh -
cd istio-1.13.3
chmod +x bin/istioctl
sudo mv bin/istioctl /usr/local/bin/istioctl

istioctl install --set profile=demo -y

echo 'Installing cluster backend capabilities'
# Cluster Backend and a couple of test deployments for noise
kubectl apply -f bootstrap/01-namespaces.yaml
sleep 5
kubectl apply -f bootstrap/02-certmanager.yaml
sleep 5
kubectl apply -f bootstrap/03-nettools-pod.yaml
sleep 5
kubectl apply -f bootstrap/04-nginx-deployment.yaml
sleep 5

echo 'Falco installation'
# Install Falco
kubectl apply -f bootstrap/falco/01-clusterrole.yaml
sleep 2
kubectl apply -f bootstrap/falco/02-serviceaccount.yaml
sleep 2
kubectl apply -f bootstrap/falco/03-clusterrolebinding.yaml
sleep 2
kubectl apply -f bootstrap/falco/04-configmap.yaml
sleep 2
kubectl apply -f bootstrap/falco/05-daemonset.yaml
sleep 2

# Install kube-bench
echo 'Installing kube-bench'
kubectl apply -f bootstrap/06-kube-bench.yaml
sleep 2
echo 'Guest book installation'

# Install Guestbook Application/Service
kubectl apply -f bootstrap/guestbook/01-guestbook.yaml
sleep 5

# Install BookInfo Istio Demo app
# istio service mesh https://istio.io/latest/docs/setup/getting-started/
echo 'Install bookinfo deployment'
kubectl apply -f bootstrap/05-bookinfo.yaml -n stg
sleep 5

#kubectl -n stg exec "$(kubectl -n stg get pod -l app=ratings -o jsonpath='{.items[0].metadata.name}')" -c ratings -- curl -sS productpage:9080/productpage | grep -o "<title>.*</title>"
echo 'Installing Kiali for istio visibility'
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.12/samples/addons/prometheus.yaml
sleep 2
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.12/samples/addons/grafana.yaml
sleep 2
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.12/samples/addons/jaeger.yaml
sleep 2
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.12/samples/addons/kiali.yaml
sleep 2
# view it with istioctl dashboard kiali

# splunk connect install
echo 'Installing Splunk Connect'
helm repo add splunk https://splunk.github.io/splunk-connect-for-kubernetes/
helm show values splunk/splunk-connect-for-kubernetes > values.yaml
helm install my-splunk-connect -f values.yaml splunk/splunk-connect-for-kubernetes





# TODO
# Install prometheus and grafana
# Install kubecost?
# install more demo applications
# install kube-hunter
# install kube-bench


echo 'Cluster setup is finished, have fun, dont forget to delete when you finish'



echo 'Running Ansible Configurations to add security tools to the instances'
echo 'Just kidding '
# TODO udpate /etc/ansible/hosts with file 