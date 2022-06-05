import yaml
import subprocess
import time
from kubernetes import client, config

# noqa: E501
# export KOPS_STATE_STORE=s3://kops-yogi-state-store/yogi.dev.us-east-1.k8s.local


class ClusterControl:
    def define_cluster_specs(self):
        with open('kops-init.yaml') as file:
            init = list(yaml.load_all(file, Loader=yaml.SafeLoader))

        init[0]['spec']['configBase'] = 's3://kops-yogi-state-store/yogi.dev.us-east-1.k8s.local'
        init[0]['spec']['sshAccess'][0] = '70.179.208.28/32'
        init[0]['spec']['kubernetesApiAccess'][0] = '70.179.208.28/32'
        init[0]['spec']['sshKeyName'] = 'kops'
        init[0]['spec']['kubelet']['anonymousAuth'] = True

        with open('dumpall.yaml', 'w') as f:
            asdf = yaml.dump_all(init, f)

    def build_cluster(self):
        # kops replace -f dumpall.yaml --force
        print('[+] Replacing cluster specs with template')
        # subprocess.run([
        #    'kops', 'replace',
        #    '-f', 'dumpall.yaml',
        #    '--state', 's3://kops-yogi-state-store/yogi.dev.us-east-1.k8s.local', '--force'])
        subprocess.run([
            'kops', 'create', '-f', 'dumpall.yaml'
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT)

        # kops update cluster --name yogi.dev.us-east-1.k8s.local --yes --admin
        print('[+] Building the cluster')
        subprocess.run([
            'kops',
            'update', 'cluster',
            '--name', 'yogi.dev.us-east-1.k8s.local',
            '--state', 's3://kops-yogi-state-store/yogi.dev.us-east-1.k8s.local',
            '--yes', '--admin'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT)

    def destroy_cluster(self):
        print('[-] Attempting to destroy the cluster')
        # kops delete cluster yogi.dev.us-east-1.k8s.local --yes
        subprocess.run([
            'kops', 'delete',
            'cluster', 'yogi.dev.us-east-1.k8s.local',
            '--state', 's3://kops-yogi-state-store/yogi.dev.us-east-1.k8s.local', '--yes'])

        # TODO clean up S3 bucket

    def get_cluster_state(self):
        # https://www.velotio.com/engineering-blog/kubernetes-python-client
        config.load_kube_config()
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        return nodes


class ClusterBackend:
    def __init__(self):
        self.core_v1 = client.CoreV1Api()

    def cert_manager_crd(self, cert_manager_version):
        # Perhaps we can make this more pythonic in the future
        # however, we'll have to split all of the compoenets apart first since there are
        # different api calls for the various components (appsv1, v1, etc.).
        # For now, it's easier to just let kubectl do the lifting here
        # config.load_kube_config()
        # cert_manager_yaml = yaml.safe_load('cert_manager.yaml')
        # apps_api = client.AppsV1Api()
        print('[+] Installing cert manager CRDs')
        cert_manager_url = f'https://github.com/jetstack/cert-manager/releases/download/v{cert_manager_version}/cert-manager.yaml'
        subprocess.run(['kubectl', 'apply', '-f', cert_manager_url])
        time.sleep(2)

    def cert_manager_secret(self):
        '''
        cert_mgr_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "ca-key-pair",
                "namespace": "dev",
                "data": {
                    "tls.crt": "",
                    "tls.key": ""
                    }}}
        try:
            self.core_v1.create_namespaced_secret(body=cert_mgr_manifest, namespace='dev')
        except Exception as e:
            print(f'!! Error attempting to create cert manager secrets, Error: {e}')
        '''
        # Using subprocess to install cert manager's secrets, and CRD type Issuer,
        # need to determine if there is a better way to install CRD objects
        subprocess.run(['kubectl', 'apply', '-f', '02-certmanager.yaml'])
        time.sleep(2)

    def build_istio(self):
        print('[+] Installing Istio')
        # istioctl install --set profile=demo -y  > /tmp/kops.log 2>&1
        subprocess.run(['istioctl', 'install', '--set', 'profile=demo', '-y'])
        time.sleep(2)

    def falco_install(self):
        print('[+] Installing Falco')
        falco_manifest = [
            '01-clusterrole.yaml',
            '02-serviceaccount.yaml',
            '03-clusterrolebinding.yaml',
            '04-configmap.yaml',
            '05-daemonset.yaml']

        for manifest in falco_manifest:
            manifest_w_path = f'../cluster_bootstrap/falco/{manifest}'
            subprocess.run(['kubectl', 'apply', '-f', manifest_w_path])
            time.sleep(2)

    def kube_bench(self):
        print('[+] Installing Kube-Bench')
        subprocess.run(['kubectl', 'apply', '-f', '../cluster_bootstrap/07-kube-bench.yaml'])
        time.sleep(2)

    def guest_book(self):
        print('[+] Installing Guestbook Application')
        subprocess.run(['kubectl', 'apply', '-f', '../cluster_bootstrap/guestbook/01-guestbook.yaml'])
        time.sleep(2)

    def book_info(self):
        print('[+] Installing Book Info Application')
        subprocess.run(['kubectl', 'apply', '-f', '../cluster_bootstrap/05-bookinfo.yaml'])
        time.sleep(2)
        subprocess.run(['kubectl', 'apply', '-f', '../cluster_bootstrap/06-bookinfo-gateway.yaml'])
        time.sleep(2)

    def kiali(self, istio_version):
        print('[+] Installing Kiali')
        subprocess.run(['kubectl', 'apply', '-f', f'https://raw.githubusercontent.com/istio/istio/release-{istio_version}/samples/addons/prometheus.yaml'])
        time.sleep(2)
        subprocess.run(['kubectl', 'apply', '-f', f'https://raw.githubusercontent.com/istio/istio/release-{istio_version}/samples/addons/grafana.yaml'])
        time.sleep(2)
        subprocess.run(['kubectl', 'apply', '-f', f'https://raw.githubusercontent.com/istio/istio/release-{istio_version}/samples/addons/jaeger.yaml'])
        time.sleep(2)
        subprocess.run(['kubectl', 'apply', '-f', f'https://raw.githubusercontent.com/istio/istio/release-{istio_version}/samples/addons/kiali.yaml'])
        time.sleep(2)

    def build_namespaces(self):
        # namespace_name: is_istio_evnoy_proxy_enabled
        namespace_names = {
            'prod': 'enabled',
            'stg': 'enabled',
            'dev': 'enabled',
            'security': 'disabled',
            'splunk-connect': 'disabled'}

        config.load_kube_config()
        for name, istio_setting in namespace_names.items():
            if istio_setting == 'enabled':
                namespace_manifest = {
                    "apiVersion": "v1",
                    "kind": "Namespace",
                    "metadata": {
                        "name": name,
                        "labels": {"istio-injection": istio_setting}}}
            else:
                namespace_manifest = {
                    "apiVersion": "v1",
                    "kind": "Namespace",
                    "metadata": {"name": name}}
            try:
                self.core_v1.create_namespace(body=namespace_manifest)
            except Exception as e:
                print(f'!! Error attempting to create namespace: {name}, Error: {e}')
            time.sleep(2)


def main():
    cluster_control = ClusterControl()
    choice = ' '
    while choice[0].lower() != 'q':
        choice = input("[B]uilding, [D]estroying or [Q]uitting? ")
        if choice[0].lower() == 'b':
            cluster_control.define_cluster_specs()

            cluster_control.build_cluster()

            timer = 600
            while timer > 0:
                try:
                    nodes = cluster_control.get_cluster_state()
                    timer = 0
                except Exception:
                    print('[ ] Waiting for Cluster to become available')
                time.sleep(60)
                timer = timer - 60
            print('[+] Cluster should be created')

            nodes = cluster_control.get_cluster_state()
            print(str(nodes))

            cluster_backend = ClusterBackend()
            print('[+] Adding assets to cluster')
            cert_manager_version = '1.8.0'
            istio_version = '1.13'
            cluster_backend.cert_manager_crd(cert_manager_version)
            cluster_backend.build_istio()
            cluster_backend.build_namespaces()
            cluster_backend.cert_manager_secret()
            cluster_backend.falco_install()
            cluster_backend.kube_bench()
            cluster_backend.guest_book()
            cluster_backend.book_info()
            cluster_backend.kiali(istio_version)

            print('[+] Cluster setup is finished. Moving on to node configuration')

            print('[+] Installing Splunk Connect for Kubernetes onto the cluster')
        elif choice[0].lower() == 'd':
            cluster_control.destroy_cluster()
        else:
            'Please pick either b to build the lab, d to destroy the lab, or q to quit'


if __name__ == "__main__":
    main()
