#!/bin/bash

set -e

################################################
# VARIABLES
################################################

# staging or prod
ENVIRONMENT=$1
# debug or release
CONFIGURATION=$2
# the functions project file
PROJECT_FILE=$(echo $TRAVIS_BUILD_DIR/src/nwayapi.csproj)
# temp resources dor packaging the code
DITRIBUTION_PATH=$(echo $TRAVIS_BUILD_DIR/dist/)
PACKAGEFILE_NAME=$(echo $ENVIRONMENT-$TRAVIS_BUILD_NUMBER.zip)
PACKAGEFILE_FULLPATH=$(echo $TRAVIS_BUILD_DIR/dist/$PACKAGEFILE_NAME)
# the assembly file generated on building
DLL_FILE=$(echo $DITRIBUTION_PATH/nwayapi.dll)
# s3 bucket destination for package
S3_PACKAGEURI=$(echo s3://$AWS_S3_PATH/$PACKAGEFILE_NAME)
# deployment code (for injecting template)
INJECTION_FILESPATH=$(echo $TRAVIS_BUILD_DIR/deploy)
INJECTIONPROJECT_FILE=$(echo $TRAVIS_BUILD_DIR/deploy/injection.csproj)
BASE_TEMPLATE=$(echo $TRAVIS_BUILD_DIR/deploy/sam-base.yml)
INJECTED_TEMPLATE=$(echo $TRAVIS_BUILD_DIR/deploy/sam-$ENVIRONMENT.yml)
BASE_STACKNAME=$(echo nway-api)
INJECTED_STACKNAME=$(echo nway-api-$ENVIRONMENT)

###############################################
# scripting
###############################################

# publish dotnet code
dotnet publish $PROJECT_FILE -o $DITRIBUTION_PATH --framework netcoreapp2.0 --runtime linux-x64 -c CONFIGURATION

# package code
zip -j $PACKAGEFILE_FULLPATH $DITRIBUTION_PATH/* 

# upload code to S3 deployment bucket
aws s3 cp $PACKAGEFILE_FULLPATH $S3_PACKAGEURI

# inject functions resources to cloudformation template
set +e
aws cloudformation describe-stacks --region us-east-1 --stack-name $INJECTED_STACKNAME --query "[Stacks[0].StackId]" --output text
if [ "$?" != "0" ]; then
    ENV_STACK_EXISTS=0
else
    ENV_STACK_EXISTS=1
fi
set -e
dotnet run --project $INJECTIONPROJECT_FILE -- $DLL_FILE $INJECTION_FILESPATH $ENVIRONMENT $TRAVIS_BUILD_NUMBER $ENV_STACK_EXISTS

# deploy base template
aws cloudformation deploy --template-file $BASE_TEMPLATE --stack-name $BASE_STACKNAME --parameter-overrides PackageFileName=$PACKAGEFILE_NAME --tags appcode=nway --no-fail-on-empty-changeset 

# deploy environment template 
aws cloudformation deploy --template-file $INJECTED_TEMPLATE --stack-name $INJECTED_STACKNAME --parameter-overrides PackageFileName=$PACKAGEFILE_NAME --tags appcode=nway --no-fail-on-empty-changeset 
