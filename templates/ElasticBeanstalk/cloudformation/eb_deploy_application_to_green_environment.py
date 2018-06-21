import boto3
import json
import traceback
import sys
import logging
import threading
import time
import io
import gzip
import shutil

from time import sleep
from datetime import datetime, timezone
from botocore.config import Config

beanstalkclient = boto3.client('elasticbeanstalk')
lambdaclient = boto3.client('lambda')

def lambda_handler_test_raise_error(event, context):
    print(event)
    raise Exception('I failed!')
    return { "EnvironmentId":"pepe" }

def lambda_handler(event, context):
    
    # event must contain:
    # { "BeanstalkApplicationName":"deployment-tests", "BeanstalkApplicationConfigurationTemplate":"AMS-D-Elast-JXD24ZW3JQ47", "S3Bucket":"mybucket", "S3Key":"/mypath/myfil.zip"}
    print(event)
    
    # to catch lambda timeout
    timer = threading.Timer((context.get_remaining_time_in_millis() / 1000.00) - 0.5, timeout, args=[event, context])
    timer.start()
    
    try:
        
        application_name = event['BeanstalkApplicationName']
        configuration_template = event['BeanstalkApplicationConfigurationTemplate']  
        s3_artifact_bucket = event['S3Bucket'] 
        s3_artifact_key = event['S3Key'] 
        
        # unique id for assets naming
        unique_id = datetime.now().isoformat('-').replace('.','-').replace(':','-')
        
        if not(environment_change_in_progress(application_name)):
            
            # get info about any existing blue environment (e.g. to get the name)
            blue_environment = get_blue_environment(application_name)
            print(blue_environment)
            
            # create a new application version
            application_version = create_application_version(application_name, unique_id, s3_artifact_bucket, s3_artifact_key)
            print(application_version)
            
            # create a green environment for the related app version
            green_environment = create_environment(application_name, application_version, configuration_template, blue_environment, unique_id)
            print(green_environment)
            
            try:
                if (blue_environment is None):
                    return { "EnvironmentId": green_environment['EnvironmentId']}
                else:
                    return { "EnvironmentId": green_environment['EnvironmentId'], "BlueEnvironmentId": blue_environment['EnvironmentId']}
            except Exception as e:
                
                print("Invoke 'arch_codepipeline_eb_terminate_environment' to delete created environment")
                terminate_environment_payload = {
                    'EnvironmentId':green_environment['EnvironmentId'],
                    'ApplicationName':application_name
                }
                
                response = lambdaclient.invoke(
                    FunctionName='arch_codepipeline_eb_terminate_environment',
                    InvocationType='Event',
                    Payload=json.dumps(terminate_environment_payload)
                )
                raise Exception('unexpected error (check the lambda logs)')

        else:
            print('Environment change in progress, cannot create a new one.')
            raise Exception('unexpected error (check the lambda logs)')
            
    except Exception as e:
        catch_exception(e)
        raise Exception('unexpected error (check the lambda logs)')

    finally:
        timer.cancel()


def catch_exception(e):
    global Status
    global Message
    
    print('Function failed due to exception.')
    e = sys.exc_info()[0]
    print(e)
    traceback.print_exc()

    return

# returns true if any environment is updating
def environment_change_in_progress(ApplicationName):
    change_status = ["Terminating","Launching","Updating"]
    response = beanstalkclient.describe_environments(
         ApplicationName=ApplicationName,
         IncludeDeleted=False
    )
 
    for environment in response['Environments']:
        if (environment['Status']) in change_status:
           return True
           
    return False  

# creates a new application version
def create_application_version(ApplicationName, UniqueId, S3Bucket, S3Key):

    response = beanstalkclient.create_application_version(
        ApplicationName=ApplicationName,
        VersionLabel=UniqueId,
        Description='created from deployment codepipeline',
        SourceBundle={
            'S3Bucket': S3Bucket,
            'S3Key': S3Key
        },
        AutoCreateApplication=False,
        Process=True
    )
    
    # current version upload status
    print(beanstalkclient.describe_application_versions(
        ApplicationName=ApplicationName,
        VersionLabels=[UniqueId]
    )['ApplicationVersions'][0]['Status'])
    
    # wait a few secs before using it ...
    sleep(5)
        
    return response  

# Returns the blue environment:
#   if no environment is found returns None
#   if multiple environments are found, returns the last updated environment
def get_blue_environment(ApplicationName):

    response = beanstalkclient.describe_environments(
         ApplicationName=ApplicationName,
         IncludeDeleted=False
    )
    
    invalid_status = ["Terminating","Terminated"]
    
    if (len(response['Environments'])==0):
        return None
    elif (len(response['Environments'])==1):
        if not(response['Environments'][0]['Status']) in invalid_status:
            return response['Environments'][0]
    else:
        mostrecent_environment = None
        mostrecent_date = datetime(1900, 1, 1, tzinfo=timezone.utc)
        for environment in response['Environments']:
            environment_date = environment['DateUpdated']
            if environment_date > mostrecent_date and not(environment['Status']) in invalid_status:
                mostrecent_environment = environment
                mostrecent_date = environment_date
        return mostrecent_environment    
            
    return None    

# Returns an environment tag value
def get_environment_tag(EnvironmentArn, TagKey):
    
    response = beanstalkclient.list_tags_for_resource(
        ResourceArn=EnvironmentArn
    )
    for tag in response['ResourceTags']:
        if (tag['Key']==TagKey):
            return tag['Value']
    return None

# Creates a new envioronment
def create_environment(ApplicationName, ApplicationVersion, ConfigTemplate, BlueEnvironment, UniqueId):
    
    if (BlueEnvironment is None):
        green_environment_name = "Environment-" + UniqueId
    else:
        green_environment_name = first_word(BlueEnvironment['EnvironmentName'],'-') + '-' + UniqueId
    
    application_version_label = ApplicationVersion['ApplicationVersion']['VersionLabel']
    print(application_version_label)
    
    response = beanstalkclient.create_environment(
        ApplicationName=ApplicationName,
        EnvironmentName=green_environment_name,
        TemplateName=ConfigTemplate,
        VersionLabel=application_version_label)
        
    return response

# writes endpoint url to output artifact (1)
def write_output(EnvironmentId, Artifact):
    
    artifact_key = Artifact['location']['s3Location']['objectKey']
    artifact_bucket = Artifact['location']['s3Location']['bucketName']
    
    config = Config(signature_version='s3v4')
    s3client = boto3.client("s3", config=config)
    
    # A GzipFile must wrap a real file or a file-like object. We do not want to
    # write to disk, so we use a BytesIO as a buffer.
    gz_body = io.BytesIO()
    gz = gzip.GzipFile(None, 'wb', 9, gz_body)
    gz.write(EnvironmentId.encode('utf-8'))  # convert unicode strings to bytes!
    gz.close()
    
    response =  s3client.put_object(
        Bucket=artifact_bucket,
        Key=artifact_key,  # Note: NO .gz extension!
        ContentType='text/plain',  # the original type
        ContentEncoding='gzip',  # MUST have or browsers will error
        Body=gz_body.getvalue()
    )
    
    return response

def first_word(input, character):
    
    for i in range(0, len(input)):
        # Count spaces in the string.
        if input[i] == character:
            return input[0:i]
    return input
    
def timeout(event, context):

    logging.error('Execution is about to time out, sending failure response to CodePipeline')
    raise Exception('unexpected error (check the lambda logs)')