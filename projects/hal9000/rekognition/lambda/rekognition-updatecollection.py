from __future__ import print_function

import boto3
import botocore

from decimal import Decimal
import json
from urllib.parse import unquote_plus

sess = boto3.Session(region_name='us-west-2')
rekognition = sess.client('rekognition')

def select_collection(path):
    if 'mateo' in path:
        return 'mateo'
    elif 'joana' in path:
        return 'joana'
    elif 'nacho' in path:
        return 'nacho'
    elif 'marta' in path:
        return 'marta'

# --------------- Main handler ------------------


def lambda_handler(event, context):

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'])
    try:
        collection = select_collection(key)
        response = rekognition.index_faces(
            CollectionId=collection,
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
        )
        coincidences = len(response['FaceRecords'])
        print({ "collection": collection, "newFaces": coincidences })
        return response

    except Exception as e:        
        return { "error": e }