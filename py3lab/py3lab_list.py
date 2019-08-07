import boto3
import botocore
import click

session = boto3.Session(profile_name='py3lab')
ec2 = session.resource('ec2')
ec2client = boto3.client('ec2')

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
#    if str(wait).lower() == 'true':
#        wait = True
#    else:
#        wait = False

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
def cli():
    """py3lab manages ec2"""
#######################################################################################################
@cli.group("instances")
def instances():
    """Commands for Instances"""
#######################################################################################################
@cli.group("volumes")
def volumes():
    """Commands for Volumes"""
#######################################################################################################
@cli.group("snapshots")
def snapshots():
    """Commands for Snapshots"""
#######################################################################################################
#######################################################################################################
#######################################################################################################
@instances.command('list')
@click.option('--project', default=None, help ='Only instances of a given project')
def list_instances(project):
    "List EC2 Instances"
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
@click.option('--wait', 'wait', default=False, is_flag=True, help ='Wait for action to complete')
def stop_instances(project,wait):
    "Stop EC2 Instances"
    toggle_instance(project,'stop',wait)
    return
#######################################################################################################
@instances.command('start')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--wait', 'wait', default=False, is_flag=True, help ='Wait for action to complete')
def start_instances(project,wait):
    "Start EC2 Instances"
    toggle_instance(project,'start',wait)
    return
#######################################################################################################
@snapshots.command('list')
@click.option('--project', default=None, help ='Only instances of a given project')
def list_snapshots(project):
    "List EC2 Snapshots"
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
@snapshots.command('create')
@click.option('--project', default=None, help ='Only instances of a given project')
def create_snapshots(project):
    "Create EC2 Snapshot"
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
@snapshots.command('delete')
@click.option('--project', default=None, help ='Only instances of a given project')
@click.option('--keep', default=1, help ='Number of Snapshots to Keep for Each Volume')
def delete_snapshots(project,wait,keep):
    "Delete EC2 Snapshot"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            snap =  list(v.snapshots.filter(Filters=[{'Name' : 'status' , 'Values' : ['completed','error']}]))
            if len(snap) > keep:
                for s1 in snap[keep:]:
                    print("Delete Snapshot {0} created on {1} from Volume {2} on Instance {3}".format(s1.id,str(s1.start_time),v.id,i.id))
                    s1.delete()
            else:
                print("No Snapshots to delete for Volume {0} on Instance {1}".format(v.id,i.id))

        #    print("Making new snapshot of instance {0}".format(i.id))

    return
#######################################################################################################
@volumes.command('list')
@click.option('--project', default=None, help ='Only instances of a given project')
def list_volumes(project,wait):
    "List EC2 Volumes"
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
@volumes.command('delete')
@click.option('--id', default=None, help ='Number of Snapshots to Keep for Each Volume')
def delete_volume(id):
    "Delete EC2 Volume - Requires Volume ID"
    volexists = len(list(ec2.volumes.filter(Filters=[{'Name' : 'volume-id' , 'Values' : [id]}])))
    if volexists > 0:
        v =  ec2.Volume(id)

        if len(v.attachments) == 1:
            vdict = dict(v.attachments[0])
            print('Detaching volume {0} from instance {1}'.format(vdict['VolumeId'],vdict['InstanceId']))
            v.detach_from_instance()
            w = ec2client.get_waiter('volume_available')
            w.wait(VolumeIds=[id])
        print('Deleting volume {0}'.format(v.id))
        v.delete()
    else:
        print('Volume {0} does not exist'.format(id))
    return
#######################################################################################################

if __name__ == '__main__':
    try:
        cli()
    except botocore.exceptions.ClientError as e:
        print("An error occured of type {0}".format(e))#
    except TypeError as e:
        print("An error occured of type {0}".format(e))
#    except:
#        print("An error occured")
