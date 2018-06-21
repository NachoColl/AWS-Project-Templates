import boto3
import json
import traceback
import sys
import logging
import threading
import time

from time import sleep
from datetime import datetime, timezone
from botocore.config import Config

beanstalkclient = boto3.client('elasticbeanstalk')
codepipelineclient = boto3.client('codepipeline')
lambdaclient = boto3.client('lambda')

Message = ""
Status  = ""

def lambda_handler(event, context):
    global Status
    global Message
    
    timer = threading.Timer((context.get_remaining_time_in_millis() / 1000.00) - 0.5, timeout, args=[event, context])
    timer.start()
    
    try:
        
        # Extract the Job ID
        job_id = event['CodePipeline.job']['id']
       
        # Extract the Job Data
        job_data = event['CodePipeline.job']['data']
        # The Artifacts
        input_artifact  = job_data['inputArtifacts'][0]
        output_artifact = job_data['outputArtifacts'][0]
        # parameters
        user_parameters = job_data['actionConfiguration']['configuration']['UserParameters']
        # { "BeanstalkApplicationName":"deployment-tests", "BeanstalkApplicationConfigurationTemplate":"AMS-D-Elast-JXD24ZW3JQ47"}
        application_name = (json.loads(user_parameters)['BeanstalkApplicationName'])
        configuration_template = (json.loads(user_parameters)['BeanstalkApplicationConfigurationTemplate'])     
        # unique id for assets naming
        unique_id = datetime.now().isoformat('-').replace('.','-').replace(':','-')
        
        if not(environment_change_in_progress(application_name)):
            
            # get info about any existing blue environment (e.g. to get the name)
            blue_environment = get_blue_environment(application_name)
            print(blue_environment)
            # create a new application version
            application_version = create_application_version(application_name, unique_id, job_id, input_artifact)
            print(application_version)
            
            # create a green environment for the related app version
            green_environment = create_environment(application_name, application_version, configuration_template, blue_environment, unique_id)
            print(green_environment)
            
            # write outputs
            try:
                print(green_environment['EnvironmentId'])
                write_output(green_environment['EnvironmentId'], event, output_artifact)
                Message = "New environment created."
                Status  = "Success"
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
                catch_exception(e)
                
        else:
            Message = "Environment change in progress."
            Status  = "Failure"
            
    except Exception as e:
        catch_exception(e)

    finally:

        timer.cancel()
        if (Status =="Success"):
            put_job_success(job_id)
        else:
            put_job_failure(job_id)

def catch_exception(e):
    global Status
    global Message
    
    print('Function failed due to exception.')
    e = sys.exc_info()[0]
    print(e)
    traceback.print_exc()
    
    Status="Failure"
    Message=("Error occured while executing this. The error is %s" %e)

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
def create_application_version(ApplicationName, UniqueId, JobId, Artifact):
    
    artifact_key = Artifact['location']['s3Location']['objectKey']
    artifact_bucket = Artifact['location']['s3Location']['bucketName']
    
    response = beanstalkclient.create_application_version(
        ApplicationName=ApplicationName,
        VersionLabel=UniqueId,
        Description='created from codepipeline job id: ' + JobId,
        SourceBundle={
            'S3Bucket': artifact_bucket,
            'S3Key': artifact_key
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
def write_output(EnvironmentId, Event, Artifact):
    
    artifact_key = Artifact['location']['s3Location']['objectKey']
    artifact_bucket = Artifact['location']['s3Location']['bucketName']
    
    config = Config(signature_version='s3v4')
    s3client = boto3.client("s3", config=config)
    
    response = s3client.put_object(
        Body=EnvironmentId, 
        Bucket=artifact_bucket, 
        Key=artifact_key, 
        ServerSideEncryption='aws:kms')
    
    return response

def first_word(input, character):
    
    for i in range(0, len(input)):
        # Count spaces in the string.
        if input[i] == character:
            return input[0:i]
    return input
    
def timeout(event, context):

    logging.error('Execution is about to time out, sending failure response to CodePipeline')
    put_job_failure(event['CodePipeline.job']['id'], "FunctionTimeOut")


def put_job_success(job):

    print('Putting job success')
    print(Message)
    codepipelineclient.put_job_success_result(jobId=job)

def put_job_failure(job):

    print('Putting job failure')
    print(Message)
    codepipelineclient.put_job_failure_result(jobId=job, failureDetails={'message': Message, 'type': 'JobFailed'})
