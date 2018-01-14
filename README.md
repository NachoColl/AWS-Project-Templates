# AWS-Project-Templates

Some AWS coding templates.

## Development Environment Setup

- [Visual Studio Code](https://code.visualstudio.com/) as the  code editor. 
    - Just download and install.
- [AWS SAM Local](https://github.com/awslabs/aws-sam-local) to run Lambda code.
    - Install [Node.js](https://nodejs.org/en/download/).
    - Install SAM Local ```npm install -g aws-sam-local```
- Some docker images to run AWS services locally.
    - Install [docker](https://www.docker.com/).
    - Run the project required images (e.g. [DynamoDB](./dockers/DynamoDB), [S3](./dockers/S3) or [LocalStack](https://github.com/localstack/localstack)).
        

## Templates

### AWS Lambda

A Lambda project using DynamoDB and S3 docker images to test code locally.

[]