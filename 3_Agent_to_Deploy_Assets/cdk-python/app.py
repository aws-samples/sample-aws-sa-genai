#!/usr/bin/env python3
import os
import aws_cdk as cdk
from biops_stack import BiopsStack

app = cdk.App()
BiopsStack(app, "BiopsStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
    )
)

app.synth()