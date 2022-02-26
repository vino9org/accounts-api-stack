from os.path import abspath, dirname

from aws_cdk import Stack
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs


from constructs import Construct


class AccountsApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def build(self):
        
        return self

    
