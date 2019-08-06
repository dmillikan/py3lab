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
    if str(wait).lower() == 'true':
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
@instances.command('list_volumes')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--wait', default=False, help ='Wait for action to complete')
def list_volumes(project,wait):
    "List EC2 Volumes"
    instance=[]
    instances = filter_instances(project)

    for i in instances:
        print("Instance {0} has the following volumes attached".format(i.id))
        print("---------------------------------------------------------------------")
        print("Volume ID \t \t \t \t \t \t \t Size")
        for v in i.volumes.all():
            print("{0} \t \t \t \t \t \t {1} GB ".format(v.id,v.size))
        print("\n \n ")
    return
#######################################################################################################
@instances.command('list_snapshots')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--wait', default=False, help ='Wait for action to complete')
def list_snapshots(project,wait):
    "List EC2 Snapshots"
    instance=[]
    instances = filter_instances(project)

    for i in instances:
        print("Instance {0} has the following snapshots".format(i.id))
        print("----------------------------------------------------------------------------------------------------------")
        print("      Volume ID \t      Snapshot ID \t \t \t Snapshot Date \t \t \t  Status")
        print("----------------------------------------------------------------------------------------------------------")
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print("{0} \t {1} \t {2} \t {3}".format(v.id,s.id,s.start_time,s.state))
        print("\n \n ")
    return
#######################################################################################################
@instances.command('create_snapshots')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--wait', default=False, help ='Wait for action to complete')
def create_snapshots(project,wait):
    "Create EC2 Snapshot"
    instance=[]
    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            snap = v.snapshots.filter(Filters=[{'Name' : 'status' , 'Values' : ['pending']}])
            for s1 in snap.all():
                print('Waiting for snapshot to complete')
                s1.wait_until_completed()

            print("Making new snapshot of instance {0}".format(i.id))
            v.create_snapshot()
    return
#######################################################################################################

@instances.command('delete_snapshots')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--wait', default=False, help ='Wait for action to complete')
@click.option('--keep', default=0, help ='Number of Snapshots to Keep for Each Volume')
def delete_snapshots(project,wait,keep):
    "Delete EC2 Snapshot"
    instance=[]
    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            snap =  list(v.snapshots.filter(Filters=[{'Name' : 'status' , 'Values' : ['completed','error']}]))
        #    for s1 in snap.all():
        #        print(v.id + '  ' + s1.id + ' '+ str(s1.start_time))
            if len(snap) > keep:
                for s1 in snap[keep:]:
                    print("Delete Snapshot {0} created on {1} from Volume {2} on Instance {3}".format(s1.id,str(s1.start_time),v.id,i.id))
                    s1.delete()
            else:
                print("No Snapshots to delete for Volume {0} on Instance {1}".format(v.id,i.id))

        #    print("Making new snapshot of instance {0}".format(i.id))

    return
#######################################################################################################


if __name__ == '__main__':
    instances()
