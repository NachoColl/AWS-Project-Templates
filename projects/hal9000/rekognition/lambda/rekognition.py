from __future__ import print_function
from urllib.parse import unquote_plus
from PIL import Image

import boto3
import botocore

import io
import uuid
import json


sess = boto3.Session(region_name='us-west-2')
rekognition = sess.client('rekognition')
s3 = sess.client('s3')
sns = sess.client('sns')

# --------------- Helper Functions ------------------

def crop_image(bucket, key, bounds):
    # get image from s3
    cur_image = s3.get_object(Bucket=bucket,Key=key)['Body'].read()
    loaded_image = Image.open(io.BytesIO(cur_image))
    width = loaded_image.size[0]
    height = loaded_image.size[1]
    # set image face coordinates
    left, upper, right, lower = bounds['Left']*width, bounds['Top']*height, (bounds['Left'] + bounds['Width'])*width, (bounds['Left'] + bounds['Height'])*height
    # crop image
    croped_image = loaded_image.crop((left,upper,right,lower))
    out_img = io.BytesIO()
    croped_image.save(out_img,'PNG')
    out_img.seek(0)  # Without this line it fails
    # set s3 path
    path = 'temp/' + key
    # save to temp s3
    s3.put_object(Bucket=bucket, Key=path, Body=out_img)
    return path
# --------------- Main handler ------------------

def lambda_handler(event, context):

    # the rekognition collections (my family ;)
    my_family = ['joana','marta','mateo','nacho']
    # will contain the identified faces...
    identified = []

    # get image bucket references
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'])

    try:

        # detect faces on image
        faces = rekognition.detect_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}})

        # loop faces
        for face in faces['FaceDetails']:
            # to pass not found faces to SNS topic also.
            found = False

            # get the face bounds.
            bounds = face['BoundingBox']

            # crop the image to face.
            face_path = crop_image(bucket,key,bounds)   

            # search face in family collections.
            for member in my_family:
                
                response = rekognition.search_faces_by_image(Image={"S3Object": {"Bucket": bucket, "Name": face_path}}, CollectionId=member, MaxFaces=1, FaceMatchThreshold=80)
                
                # if success, add member to the identified list.
                if len(response['FaceMatches'])>0:

                    # add the name of face to output list.
                    found = True
                    identified.append(member)

                    # add the new face to collection to improve success ratio.
                    rekognition.index_faces(
                        CollectionId=member,
                        Image={"S3Object": {"Bucket": bucket, "Name": face_path}}
                    )

            
            if not found:

                # if face has not been identified also send a message.
                face_url = s3.generate_presigned_url("get_object", Params = {"Bucket": bucket, "Key":face_path})
                sns.publish(
                    TopicArn='arn:aws:sns:us-west-2:882508506175:HAL9000-rekognition',
                    Message='Someone has been detected but not recognized: ' + face_url,
                    Subject='HAL message - Unrecognized face!'
                )   

            # reinizialize    
            found = False

        if (len(identified)>0):
            sns.publish(
                TopicArn='arn:aws:sns:us-west-2:882508506175:HAL9000-rekognition',
                Message=','.join(identified) + ' just entered home!',
                Subject='HAL message - Family Member(s) recognized.'
            )
            
        return identified

    except Exception as e:      
        print("Error processing object {} from bucket {}. ".format(key, bucket))
        print(e)
        return identified