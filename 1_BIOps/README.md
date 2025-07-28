## Amazon quicksight sdk SSA BIOps-scripts

Quicksight BIOps Scripts

Author: Ying Wang        Email: wangzyn@amazon.com


## Solution overview
![image](placeholder)

We provide the sample Python scripts for BIOps.
**Assets as Code:** 
How to use decribe/describe_definition APIs to run version control, and assets as code.

**Notebooks for assets deployment**
--Assets as Bundle Option:
BIOPS_QS_JSON_Option_Use_Case_1 – Using QS Assets as Bundle APIs to deploy assets across accounts or cross regions. The QS assets are in QuickSight JSON format. This notebook is only deploying one dashboard with all the dependency, without permissions. The permissions will be updated after the deployment completed. The sample code and logs are provided. Note: we are using S3 bucket to backup the JSON files.

BIOPS_CFT_Option_Use_Case_1 – Using QS Assets as Bundle APIs to deploy assets across accounts or cross regions. The QS assets are in Cloud Formation Template format. This notebook is only deploying one dashboard with all the dependency, without permissions. The permissions will be updated after the deployment completed. The sample code and logs are provided. Note: we are using S3 bucket to backup the JSON files.

[Coming soon] BIOPS_QS_JSON_Option_Use_Case_2 – Using QS Desribe Definition APIs to provide assets backup solutions.

--Template_API_Option: 
Deploy assets across accounts or cross regions with three SageMaker notebooks: 
1/Batch to deploy all the assets in one QS account
2/Incremental to deploy with an input list
3/Folder to deploy assets organized with folder(s)

--[comming soon] Describe API Option 

![image](placeholder)


## Prerequisites
For this solution, you should have the following prerequisites:

Access to the following AWS services:
o QuickSight
o SageMaker
o AWS Identity and Access Management (IAM)

Two different QuickSight accounts, for instance, development and
production

Basic knowledge of Python

Basic AWS SDK knowledge

## Create resources
Create your resources in source account by completing the following steps:

1.	Download the scripts from the GitHub repository.
2.	For notebook option, create a notebook instance.
    a.	Edit the IAM role of this instance to add an inline policy called qs-admin-source:
    ```bash
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "sts:AssumeRole",
                    "quicksight:*"
                ],
                "Resource": "*"
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Deny",
                "Action": [
                    "quicksight:DeleteA*",
                    "quicksight:DeleteC*",
                    "quicksight:DeleteD*",
                    "quicksight:DeleteG*",
                    "quicksight:DeleteI*",
                    "quicksight:DeleteN*",
                    "quicksight:DeleteTh*",
                    "quicksight:DeleteU*",
                    "quicksight:DeleteV*",
                    "quicksight:Unsubscribe"
                ],
                "Resource": "*"
            }
        ]
    }
    ```

    b.	On the notebook instance page, on the Actions menu, choose Open JupyterLab.
    c.	Upload the three notebooks into the notebook instance.
3. For python scripts
    a. Follow AWS Boto3 set up guidance to set up your local environment.
    b. Get the AWS account secrets keys and set up your local env.

## Implementing the solution
To implement the solution, complete the following steps:
Assume Role solution:
1.	Create an IAM role in the target (production) account that can be used by the source (development) account. 
2.	In the IAM console navigation pane on the left, choose Roles and then choose Create role.
3.	Choose the Another AWS account role type.
4.	For Account ID, type the source (development) account ID.
5.	Create an IAM policy called qs-admin-target:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["quicksight:*",
		      "sts:AssumeRole"],
            "Resource": "*"
        },
       {
            "Effect": "Deny",
            "Action": "quicksight:Unsubscribe",
            "Resource": "*"
        }
    ]
}
```

6.	Grant the IAM role the qs-admin-target IAM policy.

 

7.	Provide the qs-admin-source and qs-admin-target role name in Assume Role cells of the notebooks:
 

## Static Profile solution:
1.	Create IAM user qs-admin-source with policy qs-admin-source in source account.
2.	Create IAM user qs-admin-target with policy qs-admin-target in target account.
3.	Get aws_access_key_id and secret_access_key of these two IAM users.
4.	In the terminal of the SageMaker notebook, go to the directory /home/ec2-user/.aws. 
5.	Edit the config and credential file to add a profile named source with the aws_access_key_id and secret_access_key of qs-admin-source.
6.	Edit the config and credential file to add a profile named target with the aws_access_key_id and secret_access_key of qs-admin-target.
7.	Provide the source and target profile name in the Static Profile cell of the notebook:
 

The tutorials of these notebooks are provided as comments inside the notebooks. You can run it cell by cell. If you want to schedule the notebooks to run automatically, you can schedule the Jupyter notebooks on SageMaker ephemeral instances. 



## License

This library is licensed under the MIT-0 License. See the LICENSE file.