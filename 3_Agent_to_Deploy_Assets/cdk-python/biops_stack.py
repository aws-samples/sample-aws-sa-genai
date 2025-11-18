from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_s3 as s3,
    aws_cognito as cognito,
)
from constructs import Construct
import os

class BiopsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito User Pool
        user_pool = cognito.UserPool(
            self, "BiopsUserPool",
            user_pool_name="biops-users",
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Cognito User Pool Client
        user_pool_client = cognito.UserPoolClient(
            self, "BiopsUserPoolClient",
            user_pool=user_pool,
            user_pool_client_name="biops-client",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL, cognito.OAuthScope.PROFILE],
                callback_urls=["http://localhost:3000/callback", "https://localhost:3000/callback"]
            )
        )

        # Cognito User Pool Domain
        user_pool_domain = cognito.UserPoolDomain(
            self, "BiopsUserPoolDomain",
            user_pool=user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"biops-{self.account}"
            )
        )

        # DynamoDB Table
        job_table = dynamodb.Table(
            self, "JobRunsTable",
            table_name="biops-job-runs",
            partition_key=dynamodb.Attribute(name="jobId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Lambda Layer
        shared_layer = _lambda.LayerVersion(
            self, "SharedLayer",
            code=_lambda.Code.from_asset("../lambda/python"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description="Shared utilities for BIOPS Lambda functions"
        )

        # IAM Role
        lambda_role = iam.Role(
            self, "BiopsLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "BiopsPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "quicksight:*",
                                "s3:*",
                                "sts:AssumeRole",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:GetItem",
                                "dynamodb:Scan",
                                "lambda:InvokeFunction"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        # Lambda Functions
        export_function = _lambda.Function(
            self, "ExportAssetsFunction",
            function_name="biops-export-assets",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../lambda/export_assets"),
            layers=[shared_layer],
            role=lambda_role,
            timeout=Duration.minutes(5),
            environment={"DYNAMODB_TABLE": job_table.table_name}
        )

        upload_function = _lambda.Function(
            self, "UploadAssetsFunction",
            function_name="biops-upload-assets",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../lambda/upload_assets"),
            layers=[shared_layer],
            role=lambda_role,
            timeout=Duration.minutes(5),
            environment={"DYNAMODB_TABLE": job_table.table_name}
        )

        import_function = _lambda.Function(
            self, "ImportAssetsFunction",
            function_name="biops-import-assets",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../lambda/import_assets"),
            layers=[shared_layer],
            role=lambda_role,
            timeout=Duration.minutes(5),
            environment={"DYNAMODB_TABLE": job_table.table_name}
        )

        permissions_function = _lambda.Function(
            self, "UpdatePermissionsFunction",
            function_name="biops-update-permissions",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../lambda/update_permissions"),
            layers=[shared_layer],
            role=lambda_role,
            timeout=Duration.minutes(5),
            environment={"DYNAMODB_TABLE": job_table.table_name}
        )

        orchestrator_function = _lambda.Function(
            self, "OrchestratorFunction",
            function_name="biops-orchestrator",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../lambda/orchestrator"),
            layers=[shared_layer],
            role=lambda_role,
            timeout=Duration.minutes(15),
            environment={"DYNAMODB_TABLE": job_table.table_name}
        )

        job_api_function = _lambda.Function(
            self, "JobApiFunction",
            function_name="biops-job-api",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../lambda/job_api"),
            layers=[shared_layer],
            role=lambda_role,
            timeout=Duration.minutes(5),
            environment={"DYNAMODB_TABLE": job_table.table_name}
        )

        # Cognito Authorizer
        cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "BiopsAuthorizer",
            cognito_user_pools=[user_pool],
            authorizer_name="biops-authorizer"
        )

        # API Gateway
        api = apigateway.RestApi(
            self, "BiopsApi",
            rest_api_name="biops-job-api",
            description="API for BIOPS asset deployment job management",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # API Resources
        jobs_resource = api.root.add_resource("jobs")
        job_id_resource = jobs_resource.add_resource("{jobId}")
        export_resource = api.root.add_resource("export")
        export_job_id_resource = export_resource.add_resource("{exportJobId}")
        upload_resource = api.root.add_resource("upload")
        import_resource = api.root.add_resource("import")
        import_job_id_resource = import_resource.add_resource("{importJobId}")
        permissions_resource = api.root.add_resource("permissions")

        # API Methods with Cognito Authorization
        jobs_resource.add_method("GET", apigateway.LambdaIntegration(job_api_function), authorizer=cognito_authorizer)
        jobs_resource.add_method("POST", apigateway.LambdaIntegration(job_api_function), authorizer=cognito_authorizer)
        job_id_resource.add_method("GET", apigateway.LambdaIntegration(job_api_function), authorizer=cognito_authorizer)

        export_resource.add_method("POST", apigateway.LambdaIntegration(export_function), authorizer=cognito_authorizer)
        export_job_id_resource.add_method("GET", apigateway.LambdaIntegration(export_function), authorizer=cognito_authorizer)
        upload_resource.add_method("POST", apigateway.LambdaIntegration(upload_function), authorizer=cognito_authorizer)
        import_resource.add_method("POST", apigateway.LambdaIntegration(import_function), authorizer=cognito_authorizer)
        import_job_id_resource.add_method("GET", apigateway.LambdaIntegration(import_function), authorizer=cognito_authorizer)
        permissions_resource.add_method("POST", apigateway.LambdaIntegration(permissions_function), authorizer=cognito_authorizer)

        # S3 Bucket for asset storage
        asset_bucket = s3.Bucket(
            self, "AssetBucket",
            bucket_name=f"biops-version-control-demo-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Outputs
        CfnOutput(self, "ApiUrl", value=api.url, description="API Gateway endpoint URL")
        CfnOutput(self, "DynamoDBTable", value=job_table.table_name, description="DynamoDB table name")
        CfnOutput(self, "AssetBucketName", value=asset_bucket.bucket_name, description="S3 bucket for asset storage")
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id, description="Cognito User Pool ID")
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id, description="Cognito User Pool Client ID")
        CfnOutput(self, "CognitoDomain", value=user_pool_domain.domain_name, description="Cognito Domain")