DynamoDB Local docker image.

## Origin

Replicates instructions from AWS to run DynamoDB Local. 
http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html

## How to run image

```shell
docker run -p 8000:8000 nachocoll/dynamodb
```

testing: ``` aws dynamodb list-tables --endpoint-url http://localhost:8000 ```