import os.path

import aws_cdk.aws_appsync_alpha as appsync
from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

resolver_path = os.path.dirname(__file__) + "/resolvers"


class AccountsApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def build(self):
        self.accounts_table = self.make_accounts_table()
        self.transactions_table = self.make_transactions_table()
        api = self.build_appsync_accounts()

        CfnOutput(self, "AccountsApiUrl", value=api.graphql_url)
        CfnOutput(self, "AccountsTableName", value=self.accounts_table.table_name)
        CfnOutput(self, "TransactionsTableName", value=self.transactions_table.table_name)

        return self

    def build_appsync_accounts(self) -> appsync.GraphqlApi:
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

        account_ds = api.add_dynamo_db_data_source("accountDS", self.accounts_table)
        account_ds.create_resolver(
            type_name="Query",
            field_name="getAccountsForCustomer",
            request_mapping_template=appsync.MappingTemplate.dynamo_db_query(
                cond=appsync.KeyCondition.eq("customer_id", "customerId"),
            ),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )

        transactions_ds = api.add_dynamo_db_data_source("transactionDS", self.transactions_table)
        transactions_ds.create_resolver(
            type_name="Query",
            field_name="getTransactionsForAccount",
            request_mapping_template=appsync.MappingTemplate.dynamo_db_query(
                cond=appsync.KeyCondition.eq("account_id", "accountId"),
            ),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )

        return api

    def make_accounts_table(self):
        return dynamodb.Table(
            self,
            "AccountTable",
            partition_key=dynamodb.Attribute(name="customer_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

    def make_transactions_table(self):
        return dynamodb.Table(
            self,
            "TransactionTable",
            partition_key=dynamodb.Attribute(name="account_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
