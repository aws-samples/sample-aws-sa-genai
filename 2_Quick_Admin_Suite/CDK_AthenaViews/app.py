#!/usr/bin/env python3
import aws_cdk as cdk
from quick_admin_suite_athena_views.quick_admin_suite_athena_views_stack import QuickAdminSuiteAthenaViewsStack

app = cdk.App()
QuickAdminSuiteAthenaViewsStack(app, "QuickAdminSuiteAthenaViewsStack")

app.synth()