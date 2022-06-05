# Ignore this....ansible has a helm thing that looks promising
# https://docs.ansible.com/ansible/latest/collections/kubernetes/core/helm_module.html#ansible-collections-kubernetes-core-helm-module

import yaml


def configure_splunk_values(variables_to_set):
    with open('values.yaml') as f:
        doc = yaml.safe_load(f)

    doc['global']['splunk']['hec']['host'] = variables_to_set['hecHost']
    doc['global']['splunk']['hec']['host'] = variables_to_set['hecToken']
    doc['global']['splunk']['hec']['host'] = variables_to_set['hecProtocol']
    doc['global']['splunk']['hec']['host'] = variables_to_set['hecIndexName']
    doc['global']['kubernetes']['clusterName'] = variables_to_set['clusterName']

    with open('values.yaml', 'w') as f:
        yaml.safe_dump(doc, f, default_flow_style=False)


variables_to_set = {}
variables_to_set['hecHost'] = 'amazon.configure.com'
variables_to_set['hecToken'] = 'asdfasdfasdfasdf'
variables_to_set['hecProtocol'] = 'https'
variables_to_set['hecIndexName'] = 'k8s'
variables_to_set['clusterName'] = 'yogis-sandbox'
variables_to_set['prometheus_enabled'] = 'false'
variables_to_set['monitoring_agent_enabled'] = 'false'
variables_to_set['monitoring_agent_index_name'] = 'what'

configure_splunk_values(variables_to_set)
