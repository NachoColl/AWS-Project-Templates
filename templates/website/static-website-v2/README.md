# Static Website DevOps Pipeline - Version 2

This template creates a static website in AWS. 

Compared to Version 1, it uses GitHub as the repo for triggering deployment (after some tests, I don't like CodeCommit :().

## How To Use

Create a new GitHub repo using the same base strucuture as in this folder and use [cf-devops.yml](./cf-devops.yml) cloudformation teamplate to create the deployment pipeline on your AWS Account (use **us-east-1**, as the related website SSL Certificate must get issued in us-east-1).

To get GitHub webhooks you will require to create a secret token and use it as a secret parameter on the cf-devops.yml cf template.

Enjoy!






