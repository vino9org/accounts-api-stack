import os.path

import aws_cdk.aws_appsync_alpha as appsync
from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_events as events
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_sam as sam
from aws_solutions_constructs.aws_eventbridge_lambda import EventbridgeToLambda
from aws_solutions_constructs.aws_lambda_dynamodb import LambdaToDynamoDB
from constructs import Construct

resolver_path = os.path.abspath(os.path.dirname(__file__) + "/resolvers")


class AccountsApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def build(self):
        cons = self.dynamodb_table_for_lambda()
        api = self.build_appsync_accounts(cons.dynamo_table)
        self.event_bridge_trigger_for_lambda(cons.lambda_function)

        CfnOutput(self, "AccountsApiUrl", value=api.graphql_url)
        CfnOutput(self, "AccountsTableName", value=cons.dynamo_table.table_name)

        return self

    def build_appsync_accounts(self, ddb_table: dynamodb.Table) -> appsync.GraphqlApi:
        schema_dir = os.path.abspath(os.path.dirname(__file__))
        api = appsync.GraphqlApi(
            self,
            "Api",
            name="accounts",
            schema=appsync.Schema.from_asset(f"{schema_dir}/schema.graphql"),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(authorization_type=appsync.AuthorizationType.IAM)
            ),
            xray_enabled=True,
            log_config=appsync.LogConfig(
                field_log_level=appsync.FieldLogLevel.ALL,
            ),
        )
        api.apply_removal_policy(RemovalPolicy.DESTROY)

        account_ds = api.add_dynamo_db_data_source("accountDS", ddb_table)
        account_ds.create_resolver(
            type_name="Query",
            field_name="getAccountsForCustomer",
            request_mapping_template=appsync.MappingTemplate.from_file(
                f"{resolver_path}/get_accounts_for_customer.vtl"
            ),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )
        account_ds.create_resolver(
            type_name="Query",
            field_name="getTransactionsForAccount",
            request_mapping_template=appsync.MappingTemplate.dynamo_db_query(
                cond=appsync.KeyCondition.eq("id", "accountId")
            ),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )

        return api

    def dynamodb_table_for_lambda(self) -> LambdaToDynamoDB:
        """
        use single table to store both account info and transactions
        for account record, the hash key is customer_id, sort key is account_id
        for transaction record, hash key is account_id, sort key is transaction_id
        """
        src_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../runtime")
        return LambdaToDynamoDB(
            self,
            f"{self.stack_name}-AccountsTable",
            dynamo_table_props=dynamodb.TableProps(
                partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
                sort_key=dynamodb.Attribute(name="sid", type=dynamodb.AttributeType.STRING),
                billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                removal_policy=RemovalPolicy.DESTROY,
            ),
            lambda_function_props=_lambda.FunctionProps(
                runtime=_lambda.Runtime.PYTHON_3_9,
                handler="app.lambda_handler",
                code=_lambda.Code.from_asset(src_dir),
                layers=[self.powertools_layer("1.24.2")],
                memory_size=512,
                architecture=_lambda.Architecture.ARM_64,
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
        )

    def event_bridge_trigger_for_lambda(self, lambda_func: _lambda.Function) -> EventbridgeToLambda:
        return EventbridgeToLambda(
            self,
            f"{self.stack_name}-trigger",
            existing_lambda_obj=lambda_func,
            event_rule_props=events.RuleProps(
                enabled=True,
                event_pattern=events.EventPattern(
                    source=["service.fund_transfer"], detail_type=["transfer"], detail={"status": ["completed"]}
                ),
                rule_name=f"{self.stack_name}-update-trigger",
            ),
        )

    def powertools_layer(self, version: str) -> _lambda.ILayerVersion:
        # Launches SAR App as CloudFormation nested stack and return Lambda Layer
        POWERTOOLS_BASE_NAME = "AWSLambdaPowertools"
        powertools_app = sam.CfnApplication(
            self,
            f"{POWERTOOLS_BASE_NAME}Application",
            location={
                "applicationId": "arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer-extras",  # noqa
                "semanticVersion": version,
            },
        )
        powertools_layer_arn = powertools_app.get_att("Outputs.LayerVersionArn").to_string()
        return _lambda.LayerVersion.from_layer_version_arn(self, f"{POWERTOOLS_BASE_NAME}", powertools_layer_arn)
