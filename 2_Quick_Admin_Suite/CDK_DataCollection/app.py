#!/usr/bin/env python3
import aws_cdk as cdk
from quick_admin_suite_data_collection.quick_admin_suite_data_collection_stack import QuickAdminSuiteDataCollectionStack

app = cdk.App()
QuickAdminSuiteDataCollectionStack(app, "QuickAdminSuiteDataCollectionStack")

app.synth()