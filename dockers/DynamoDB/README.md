DynamoDB Local docker image.

## Origin

Replicates instructions from AWS to install and run DynamoDB locally. 
http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html

## How to run image

### Ephimeral data

```shell
docker run -p 8000:8000 nachocoll/dynamodb
```

### Persistent data

```shell
docker run -v /my-directory:/data -p 8000:8000 nachocoll/dynamodb
```



