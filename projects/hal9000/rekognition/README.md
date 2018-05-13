# HAL9000

A Weekend Project for testing some AWS Rekognition features.

## Description

[Project notes on LinkedIn](https://www.linkedin.com/pulse/using-aws-rekognition-detect-your-childs-arrived-home-nacho-coll/)


### Testing Locally

``` bash
sam local generate-event s3 --bucket project-hal-s3-ftp  --key face-collections/nacho/WIN_20180506_18_28_08_Pro.jpg | sam local invoke RekognitionUpdateCollectionLambda --profile nachocoll
```

``` bash
sam local generate-event s3 --bucket project-hal-s3-ftp  --key face-collections/nacho/WIN_20180506_18_28_08_Pro.jpg | sam local invoke RekognitionLambda --profile nachocoll
```

[How to install PIL library](https://learn-serverless.org/post/deploying-pillow-aws-lambda/)