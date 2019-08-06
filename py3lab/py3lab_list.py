import boto3
import click

session = boto3.Session(profile_name='py3lab')
ec2 = session.resource('ec2')

#######################################################################################################
def filter_instances(project):
    if project:
        filters = [{'Name': 'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    instances
    return instances
#######################################################################################################
def toggle_instance(project,reqState,wait):
    instance=[]
    instances = filter_instances(project)
    if wait.lower() == 'true':
        wait = True
    else:
        wait = False

    for i in instances:
        curState = i.state['Name']

        if not i.spot_instance_request_id:
            if reqState == 'stop' and curState == 'running':
                print("Stopping {0}.....".format(i.id))
                i.stop()
                if wait:
                    i.wait_until_stopped()
            elif reqState == 'start' and curState == 'stopped':
                print("Starting {0}....".format(i.id))
                i.start()
                if wait:
                    i.wait_until_running()
            else:
                print("Cannot {0} instance {1} \n \tInstance is currently {2}".format(reqState,i.id,i.state['Name']))
        else:
            print("Cannot start or stop instance {0} as it is a spot instance".format(i.id))

    return
#######################################################################################################
#######################################################################################################
#######################################################################################################
@click.group()
def instances():
    """Commands for Instances"""
#######################################################################################################
#######################################################################################################
@instances.command('list')
@click.option('--project', default=None, help ='Only instances of a given project')
def list_instances(project):
    "List EC2 Instances"
    instance=[]

    instances = filter_instances(project)
    for i in instances:
        tags = { t['Key'] : t['Value'] for t in i.tags or [] }
        if i.spot_instance_request_id :
            isspot = 'Is Spot Instance'
        else:
            isspot = 'Is Not Spot Instance'
        print(','.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            str(i.spot_instance_request_id),
            isspot,
            tags.get('Project','<no project>')

        )))
    return


#######################################################################################################
@instances.command('stop')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--wait', default=False, help ='Wait for action to complete')
def stop_instances(project,wait):
    "Stop EC2 Instances"
    toggle_instance(project,'stop',wait)
    return
#######################################################################################################
@instances.command('start')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--wait', default=False, help ='Wait for action to complete')
def start_instances(project,wait):
    "Start EC2 Instances"
    toggle_instance(project,'start',wait)
    return
#######################################################################################################


#######################################################################################################
@click.group()
def snapshots():
    """Commands for Snapshots"""
#######################################################################################################
@snapshots.command('start')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--wait', default=False, help ='Wait for action to complete')
def list_snapshots(project,wait):
    "List EC2 Snapshots"
    print('Let us see if this works')
    return
#######################################################################################################



if __name__ == '__main__':
    instances()
    
