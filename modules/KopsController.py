import os
import re
import yaml
import subprocess
import time
from kubernetes import client, config

# let python build the kops cluster
# we still need to adjust the config file and edit it dynamically


class KopsController():

    def __init__(self, config):
        self.config = config

        custom_dict = self.config.copy()
        variables = dict()
        variables['config'] = custom_dict

    def define_cluster_specs(self):
        blah = os.listdir()
        print(blah)

        with open('kubernetes/kops/kops-init.yaml') as file:
            init = list(yaml.load_all(file, Loader=yaml.SafeLoader))

        init[0]['spec']['configBase'] = self.config['config_base']
        init[0]['spec']['sshAccess'][0] = self.config['ip_whitelist']
        init[0]['spec']['kubernetesApiAccess'][0] = self.config['ip_whitelist']
        # init[0]['spec']['sshKeyName'] = self.config['public_key_path']
        if self.config['k8s_anon_kubelet']:
            anon_kubelet = True
        else: 
            anon_kubelet = False
        init[0]['spec']['kubelet']['anonymousAuth'] = anon_kubelet
        # init[0]['metadata']['name'] = self.config['range_name']
        # init[1]['metadata']['labels']['kops.k8s.io/cluster'] = self.config['range_name']
        # init[2]['metadata']['labels']['kops.k8s.io/cluster'] = self.config['range_name']

        print(str(init))
        print('init values are above')
        with open('kubernetes/kops/dumpall.yaml', 'w') as f:
            asdf = yaml.dump_all(init, f)

    def build_cluster(self):
        #self.log.info("[action] > build\n")
        # kops replace -f dumpall.yaml --force
        print('[+] Replacing cluster specs with template')
        # subprocess.run([
        #    'kops', 'replace',
        #    '-f', 'dumpall.yaml',
        #    '--state', 's3://kops-yogi-state-store/yogi.dev.us-east-1.k8s.local', '--force'])
        subprocess.run([
            'kops', 'create', '-f', 'kubernetes/kops/dumpall.yaml'
            ])

        # kops update cluster --name yogi.dev.us-east-1.k8s.local --yes --admin
        print('[+] Building the cluster')
        subprocess.run([
            'kops',
            'update', 'cluster',
            '--name', 'yogi.dev.us-east-1.k8s.local',
            '--state', 's3://kops-yogi-state-store/yogi.dev.us-east-1.k8s.local',
            '--yes', '--admin'])

    def destroy_cluster(self):
        # self.log.info("[action] > destroy\n")
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
    '''
    def build(self):
        self.log.info("[action] > build\n")
        cwd = os.getcwd()
        os.system('cd ' + os.path.join(os.path.dirname(__file__), '../terraform', self.config['provider'], self.config['tf_backend']) + ' && terraform init ')
        os.system('cd ' + cwd)
        return_code, stdout, stderr = self.terraform.apply(
            capture_output='yes', skip_plan=True, no_color=IsNotFlagged)
        if not return_code:
            self.log.info(
                "attack_range has been built using terraform successfully")
            self.list_machines()

    def destroy(self):
        self.log.info("[action] > destroy\n")
        cwd = os.getcwd()
        os.system('cd ' + os.path.join(os.path.dirname(__file__), '../terraform', self.config['provider'], self.config['tf_backend']) + ' && terraform init ')
        os.system('cd ' + cwd)
        return_code, stdout, stderr = self.terraform.destroy(
            capture_output='yes', no_color=IsNotFlagged, force=IsNotFlagged, auto_approve=True)
        self.log.info("Destroyed with return code: " + str(return_code))
        statepath = self.config["statepath"]
        statebakpath = self.config["statepath"] + ".backup"
        if os.path.exists(statepath) and return_code==0:
            try:
                os.remove(statepath)
                os.remove(statebakpath)
            except Exception as e:
                self.log.error("not able to delete state file")
        self.log.info(
            "attack_range has been destroy using terraform successfully")

    def stop(self):
        if self.config['provider'] == 'aws':
            instances = aws_service.get_all_instances(self.config)
            aws_service.change_ec2_state(instances, 'stopped', self.log, self.config)
        elif self.config['provider'] == 'azure':
            azure_service.change_instance_state(self.config, 'stopped', self.log)

    def resume(self):
        if self.config['provider'] == 'aws':
            instances = aws_service.get_all_instances(self.config)
            aws_service.change_ec2_state(instances, 'running', self.log, self.config)
        elif self.config['provider'] == 'azure':
            azure_service.change_instance_state(self.config, 'running', self.log)
    '''
