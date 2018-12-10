S3 Docker Image.

## Origin

S3rver service: https://github.com/jamhall/s3rver

## How to run the image

```shell
docker run -p 8001:8001 nachocoll/s3
```

### How to init C# SDK client

```csharp
 static protected TransferUtility AWSS3TransferUtility = 
      new TransferUtility(new AmazonS3Client(new AmazonS3Config() { 
              RegionEndpoint=RegionEndpoint.USWest2,
              ServiceURL= @"http://localhost:8002",
              UseHttp = true,
              ForcePathStyle = true,
              SignatureVersion ="2"
      })); 
```



