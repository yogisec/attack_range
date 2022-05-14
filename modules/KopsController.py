import os
import re

# let pythong build the kops cluster
# we still need to adjust the config file and edit it dynamically

class KopsController(IEnvironmentController):

    def __init__(self, config, log):
        super().__init__(config, log)
        statefile = self.config['range_name'] + ".terraform.tfstate"
        if self.config['provider'] == 'aws':
            self.config["statepath"] = os.path.join(os.path.dirname(__file__), '../terraform/aws/local/state', statefile)
        elif self.config['provider'] == 'azure':
            self.config["statepath"] = os.path.join(os.path.dirname(__file__), '../terraform/azure/local/state', statefile)

        self.config['splunk_es_app_version'] = re.findall(r'\d+', self.config['splunk_es_app'])[0]

        custom_dict = self.config.copy()
        variables = dict()
        variables['config'] = custom_dict

        if self.config['tf_backend'] == 'remote':
            with open(os.path.join(os.path.dirname(__file__), '../terraform', self.config['provider'], 'remote/resources.tf.j2'), 'r') as file :
                filedata = file.read()

            filedata = filedata.replace('[region]', self.config['region'])
            filedata = filedata.replace('[backend]', self.config['tf_backend_name'])
            filedata = filedata.replace('[tf_backend_ressource_group]', self.config['tf_backend_ressource_group'])
            filedata = filedata.replace('[tf_backend_storage_account]', self.config['tf_backend_storage_account'])
            filedata = filedata.replace('[tf_backend_container]', self.config['tf_backend_container'])

            with open(os.path.join(os.path.dirname(__file__), '../terraform', self.config['provider'], 'remote/resources.tf'), 'w+') as file:
                file.write(filedata)
        working_dir = os.path.join(os.path.dirname(__file__), '../terraform', self.config['provider'], self.config['tf_backend'])

        self.terraform = Terraform(working_dir=working_dir,variables=variables, parallelism=15 ,state=config.get("statepath"))


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