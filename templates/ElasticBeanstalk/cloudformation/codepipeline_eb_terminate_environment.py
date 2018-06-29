import boto3
import json
import traceback
import sys
import logging
import threading
import time

from time import sleep
from datetime import datetime, timezone

beanstalkclient = boto3.client('elasticbeanstalk')
lambdaclient = boto3.client('lambda')

def lambda_handler(event, context):

    print(event)

    timer = threading.Timer((context.get_remaining_time_in_millis() / 1000.00) - 60, timeout, args=[event, context])
    timer.start()
    
    try:

        while (environment_launch_in_progress(event['ApplicationName'], event['EnvironmentId'])):
            sleep(5)
        
        delete_environment(event['EnvironmentId'])
        
    except Exception as e:
        catch_exception(e)

    finally:
        timer.cancel()


# returns true if any environment is updating
def environment_launch_in_progress(ApplicationName, EnvironmentId):
    change_status = ["Launching", "Updating"]
    
    response = beanstalkclient.describe_environments(
         ApplicationName=ApplicationName,
         IncludeDeleted=False
    )
 
    for environment in response['Environments']:
        print(environment)    
        if environment['Status'] in change_status and environment['EnvironmentId'] == EnvironmentId:
           return True
           
    return False  



# deletes an environment
def delete_environment(EnvironmentId):
    print(EnvironmentId)
    print("Deleting environment ...")
    
    if not (EnvironmentId is None):
        response = beanstalkclient.terminate_environment(
            EnvironmentId=EnvironmentId,
            TerminateResources=True
        )
        
    return 

def timeout(event, context):
    
    print("Timeout")
    print(event)

    # if we had no time to terminate the environment, we call again ourself.
    if environment_launch_in_progress(event['ApplicationName'], event['EnvironmentId']):
        print("Recurse call to me!")
        response = lambdaclient.invoke(
            FunctionName=context['invoked_function_arn'],
            InvocationType='Event',
            ClientContext=context,
            Payload=event
        )
        
    return   
    
def catch_exception(e):

    print('Function failed due to exception.')
    e = sys.exc_info()[0]
    print(e)
    traceback.print_exc()
    
    return