import os.path
from typing import Tuple

import aws_cdk.aws_appsync_alpha as appsync
from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

resolver_path = os.path.dirname(__file__) + "/resolvers"


class AccountsApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def build(self):
        api, table = self.build_appsync_accounts()
        CfnOutput(self, "AccountsApiUrl", value=api.graphql_url)
        CfnOutput(self, "AccountsTableName", value=table.table_name)
        return self

    def build_appsync_accounts(self) -> Tuple[appsync.GraphqlApi, dynamodb.Table]:
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

        account_table = dynamodb.Table(
            self,
            "AccountTable",
            partition_key=dynamodb.Attribute(name="customer_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        account_dS = api.add_dynamo_db_data_source("accountDS", account_table)

        account_dS.create_resolver(
            type_name="Query",
            field_name="getAccountsForCustomer",
            request_mapping_template=appsync.MappingTemplate.from_file(
                f"{resolver_path}/get_accounts_for_customer.vtl"
            ),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )

        return api, account_table
