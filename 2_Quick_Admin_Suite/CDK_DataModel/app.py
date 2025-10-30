#!/usr/bin/env python3
import aws_cdk as cdk
from quick_admin_suite_data_model.quick_admin_suite_data_model_stack import QuickAdminSuiteDataModelStack

app = cdk.App()
QuickAdminSuiteDataModelStack(app, "QuickAdminSuiteDataModelStack")

app.synth()