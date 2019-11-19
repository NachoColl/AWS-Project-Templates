# Static Website DevOps Pipeline

This template creates a static website pipeline in AWS.

Some notes [here](https://www.linkedin.com/pulse/devops-setup-automation-nacho-coll/).


## Deploy

You must launch this stack in **us-east-1**, as the related website SSL Certificate can only be used with CloudFront in us-east-1!

Also note that project developer IAM user is created but you need to manually grant access by setting a CodeCommit username/password or SSH.

[![Launch in AWS](https://s3.amazonaws.com/www.devopsessentialsaws.com/img/deploy-to-aws.png)](https://console.aws.amazon.com/cloudformation/home?#/stacks/new?templateURL=https://s3-us-west-2.amazonaws.com/cloudformation-templates.nachocoll/StaticWebsite/StaticWebsite_DevOps.yaml)


## References

Eric Hammond [template for static websites](https://github.com/alestic/aws-git-backed-static-website).

Paul Duval [example templates](https://github.com/stelligent/devops-essentials/tree/master/samples).