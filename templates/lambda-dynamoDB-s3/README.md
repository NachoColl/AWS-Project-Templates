 A simple lambda function that uploads a file to S3 then adds a record to dynamoDB.

 ## Project Setup

 ### Run S3 and DynamoDB docker images

 Change "my-local-path-x" with your own local machine directories.

```docker run -v /my-local-path-for-S3:/data -p 8001:8001 nachocoll/s3```

![run s3 docker image](/assets/images/docker-run-s3.JPG)

```docker run -v /my-local-path-for-DynamoDB:/data -p 8000:8000 nachocoll/dynamodb```

![run s3 docker image](/assets/images/docker-run-dynamodb.JPG)

### Test the services connectivity

Check S3 service

```aws --endpoint http://127.0.0.1:8001 --region localhost s3 ls```

![run s3 docker image](/assets/images/docker-running-s3.JPG)

Check the DynamoDB service

```aws --endpoint http://127.0.0.1:8000 --region localhost dynamodb list-tables```

![run s3 docker image](/assets/images/docker-running-dynamodb.JPG)

### Running the Lambda code



### Test the results









