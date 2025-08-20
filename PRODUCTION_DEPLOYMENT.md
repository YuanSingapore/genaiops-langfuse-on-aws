# Production Deployment Guide

## 🚀 Production Architecture

### Recommended Production Setup

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   AWS Lambda    │───▶│   AWS Bedrock   │
│   Load Balancer │    │   (API Layer)   │    │  (Foundation    │
│   (ALB/CloudFront)│    │                 │    │   Models)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudWatch    │    │   Langfuse      │    │   AWS Secrets   │
│   (Metrics)     │    │ (Observability) │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Infrastructure as Code (CloudFormation)

```yaml
# infrastructure.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'GenAI MLOps with Langfuse Production Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]
  
  LangfuseHost:
    Type: String
    Description: Langfuse instance URL
  
  LangfuseSecretKey:
    Type: String
    NoEcho: true
    Description: Langfuse secret key

Resources:
  # Secrets Manager for Langfuse credentials
  LangfuseSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: !Sub 'LangFuse-LLM-monitoring-${Environment}'
      Description: 'Langfuse API credentials for LLM monitoring'
      SecretString: !Sub |
        {
          "LANGFUSE_SECRET_KEY": "${LangfuseSecretKey}",
          "LANGFUSE_PUBLIC_KEY": "${LangfusePublicKey}",
          "LANGFUSE_HOST": "${LangfuseHost}"
        }

  # IAM Role for Lambda execution
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: BedrockAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - bedrock:InvokeModel
                  - bedrock:InvokeModelWithResponseStream
                  - bedrock:ListFoundationModels
                Resource: '*'
              - Effect: Allow
                Action:
                  - secretsmanager:GetSecretValue
                Resource: !Ref LangfuseSecret

  # Lambda function for GenAI processing
  GenAIProcessorFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub 'genai-processor-${Environment}'
      Runtime: python3.11
      Handler: lambda_function.lambda_handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Timeout: 300
      MemorySize: 1024
      Environment:
        Variables:
          ENVIRONMENT: !Ref Environment
          LANGFUSE_SECRET_NAME: !Ref LangfuseSecret
          AWS_REGION: !Ref AWS::Region
      Code:
        ZipFile: |
          # Lambda function code will be deployed separately
          def lambda_handler(event, context):
              return {"statusCode": 200, "body": "Function deployed"}

  # API Gateway for REST API
  GenAIApi:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: !Sub 'genai-api-${Environment}'
      Description: 'GenAI MLOps API with Langfuse observability'
      EndpointConfiguration:
        Types:
          - REGIONAL

  # CloudWatch Log Group
  GenAILogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/lambda/genai-processor-${Environment}'
      RetentionInDays: 30

  # CloudWatch Alarms
  HighErrorRateAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub 'GenAI-HighErrorRate-${Environment}'
      AlarmDescription: 'High error rate in GenAI processing'
      MetricName: Errors
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 2
      Threshold: 10
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: FunctionName
          Value: !Ref GenAIProcessorFunction

Outputs:
  LambdaFunctionArn:
    Description: 'Lambda function ARN'
    Value: !GetAtt GenAIProcessorFunction.Arn
    Export:
      Name: !Sub '${AWS::StackName}-LambdaArn'
  
  ApiGatewayUrl:
    Description: 'API Gateway URL'
    Value: !Sub 'https://${GenAIApi}.execute-api.${AWS::Region}.amazonaws.com'
    Export:
      Name: !Sub '${AWS::StackName}-ApiUrl'
```

### Lambda Function Implementation

```python
# lambda_function.py
import json
import os
import boto3
from typing import Dict, Any
import logging

# Import your utilities
from utils import converse, get_secret
from config import MODEL_CONFIG, GUARDRAIL_CONFIG

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for GenAI processing with Langfuse observability
    """
    
    try:
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Extract parameters
        messages = body.get('messages', [])
        model_id = body.get('model_id', 'us.amazon.nova-lite-v1:0')
        use_guardrails = body.get('use_guardrails', True)
        
        # Validate input
        if not messages:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Messages are required'})
            }
        
        # Prepare generation parameters
        generation_params = {
            'messages': messages,
            'model_id': model_id,
            'metadata': {
                'environment': os.getenv('ENVIRONMENT', 'production'),
                'request_id': context.aws_request_id,
                'function_name': context.function_name
            }
        }
        
        # Add model-specific configuration
        if model_id in MODEL_CONFIG:
            generation_params.update(MODEL_CONFIG[model_id])
        
        # Add guardrails if requested
        if use_guardrails:
            generation_params['guardrailConfig'] = GUARDRAIL_CONFIG
        
        # Generate response
        response_text = converse(**generation_params)
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': response_text,
                'model_id': model_id,
                'request_id': context.aws_request_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'request_id': context.aws_request_id if context else None
            })
        }
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy GenAI MLOps Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=utils --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Deploy CloudFormation stack
        run: |
          aws cloudformation deploy \
            --template-file infrastructure.yaml \
            --stack-name genai-mlops-staging \
            --parameter-overrides \
              Environment=staging \
              LangfuseHost=${{ secrets.LANGFUSE_HOST }} \
              LangfuseSecretKey=${{ secrets.LANGFUSE_SECRET_KEY }} \
            --capabilities CAPABILITY_IAM
      
      - name: Package and deploy Lambda
        run: |
          zip -r lambda-package.zip utils.py config.py lambda_function.py
          aws lambda update-function-code \
            --function-name genai-processor-staging \
            --zip-file fileb://lambda-package.zip

  deploy-production:
    needs: [test, deploy-staging]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Deploy to production
        run: |
          aws cloudformation deploy \
            --template-file infrastructure.yaml \
            --stack-name genai-mlops-production \
            --parameter-overrides \
              Environment=production \
              LangfuseHost=${{ secrets.LANGFUSE_HOST }} \
              LangfuseSecretKey=${{ secrets.LANGFUSE_SECRET_KEY }} \
            --capabilities CAPABILITY_IAM
```

## 📊 Monitoring & Alerting

### CloudWatch Dashboards

```python
# monitoring/dashboard.py
import boto3
import json

def create_genai_dashboard():
    """Create CloudWatch dashboard for GenAI monitoring"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", "FunctionName", "genai-processor-production"],
                        [".", "Errors", ".", "."],
                        [".", "Duration", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Lambda Metrics"
                }
            },
            {
                "type": "log",
                "properties": {
                    "query": "SOURCE '/aws/lambda/genai-processor-production'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100",
                    "region": "us-east-1",
                    "title": "Recent Errors"
                }
            }
        ]
    }
    
    cloudwatch.put_dashboard(
        DashboardName='GenAI-MLOps-Production',
        DashboardBody=json.dumps(dashboard_body)
    )
```

### Custom Metrics

```python
# monitoring/custom_metrics.py
import boto3
from datetime import datetime

class CustomMetrics:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
    
    def put_token_usage_metric(self, model_id: str, input_tokens: int, output_tokens: int):
        """Send token usage metrics to CloudWatch"""
        
        self.cloudwatch.put_metric_data(
            Namespace='GenAI/TokenUsage',
            MetricData=[
                {
                    'MetricName': 'InputTokens',
                    'Dimensions': [
                        {'Name': 'ModelId', 'Value': model_id}
                    ],
                    'Value': input_tokens,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'OutputTokens',
                    'Dimensions': [
                        {'Name': 'ModelId', 'Value': model_id}
                    ],
                    'Value': output_tokens,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    
    def put_cost_metric(self, model_id: str, cost: float):
        """Send cost metrics to CloudWatch"""
        
        self.cloudwatch.put_metric_data(
            Namespace='GenAI/Cost',
            MetricData=[
                {
                    'MetricName': 'EstimatedCost',
                    'Dimensions': [
                        {'Name': 'ModelId', 'Value': model_id}
                    ],
                    'Value': cost,
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )

# Usage in your Lambda function
metrics = CustomMetrics()

@observe(as_type="generation", name="Production Generation")
def production_generate(messages, model_id, **kwargs):
    response = converse(messages, model_id=model_id, **kwargs)
    
    # Send custom metrics
    if hasattr(langfuse_context, '_current_observation'):
        usage = langfuse_context._current_observation.usage
        if usage:
            metrics.put_token_usage_metric(
                model_id=model_id,
                input_tokens=usage.get('input', 0),
                output_tokens=usage.get('output', 0)
            )
            
            # Calculate and send cost metrics
            cost = calculate_cost(usage, model_id)
            metrics.put_cost_metric(model_id=model_id, cost=cost)
    
    return response
```

## 🔒 Security Hardening

### Environment-Specific Configuration

```python
# config/production.py
import os

class ProductionConfig:
    # Security settings
    ENABLE_GUARDRAILS = True
    LOG_LEVEL = "INFO"  # Don't log DEBUG in production
    MASK_PII = True
    
    # Performance settings
    MAX_CONCURRENT_REQUESTS = 100
    REQUEST_TIMEOUT = 30
    CACHE_TTL = 3600
    
    # Model settings
    DEFAULT_MODEL = "us.amazon.nova-lite-v1:0"
    FALLBACK_MODEL = "us.amazon.nova-micro-v1:0"
    
    # Monitoring
    ENABLE_DETAILED_MONITORING = True
    ALERT_ON_HIGH_COST = True
    COST_THRESHOLD_USD = 100.0

class DevelopmentConfig:
    # More permissive settings for development
    ENABLE_GUARDRAILS = False
    LOG_LEVEL = "DEBUG"
    MASK_PII = False
    
    # Performance settings
    MAX_CONCURRENT_REQUESTS = 10
    REQUEST_TIMEOUT = 60
    CACHE_TTL = 300
    
    # Model settings
    DEFAULT_MODEL = "us.amazon.nova-micro-v1:0"  # Cheaper for dev
    FALLBACK_MODEL = "us.amazon.nova-micro-v1:0"

# Select configuration based on environment
config = ProductionConfig() if os.getenv('ENVIRONMENT') == 'production' else DevelopmentConfig()
```

### WAF Rules for API Gateway

```yaml
# waf-rules.yaml
WebACL:
  Type: AWS::WAFv2::WebACL
  Properties:
    Name: !Sub 'GenAI-API-Protection-${Environment}'
    Scope: REGIONAL
    DefaultAction:
      Allow: {}
    Rules:
      - Name: RateLimitRule
        Priority: 1
        Statement:
          RateBasedStatement:
            Limit: 1000
            AggregateKeyType: IP
        Action:
          Block: {}
        VisibilityConfig:
          SampledRequestsEnabled: true
          CloudWatchMetricsEnabled: true
          MetricName: RateLimitRule
      
      - Name: SQLInjectionRule
        Priority: 2
        Statement:
          SqliMatchStatement:
            FieldToMatch:
              Body: {}
            TextTransformations:
              - Priority: 0
                Type: URL_DECODE
        Action:
          Block: {}
        VisibilityConfig:
          SampledRequestsEnabled: true
          CloudWatchMetricsEnabled: true
          MetricName: SQLInjectionRule
```

## 📈 Scaling Considerations

### Auto Scaling Configuration

```python
# scaling/auto_scaling.py
import boto3
from typing import Dict, Any

class AutoScalingManager:
    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.application_autoscaling = boto3.client('application-autoscaling')
    
    def configure_lambda_concurrency(self, function_name: str, reserved_concurrency: int):
        """Configure Lambda reserved concurrency"""
        
        self.lambda_client.put_reserved_concurrency_configuration(
            FunctionName=function_name,
            ReservedConcurrencyLimit=reserved_concurrency
        )
    
    def setup_provisioned_concurrency(self, function_name: str, version: str, concurrency: int):
        """Setup provisioned concurrency for consistent performance"""
        
        self.lambda_client.put_provisioned_concurrency_config(
            FunctionName=function_name,
            Qualifier=version,
            ProvisionedConcurrencyLimit=concurrency
        )
    
    def create_scaling_policy(self, function_name: str):
        """Create auto-scaling policy based on utilization"""
        
        # Register scalable target
        self.application_autoscaling.register_scalable_target(
            ServiceNamespace='lambda',
            ResourceId=f'function:{function_name}:provisioned',
            ScalableDimension='lambda:function:ProvisionedConcurrency',
            MinCapacity=1,
            MaxCapacity=100
        )
        
        # Create scaling policy
        self.application_autoscaling.put_scaling_policy(
            PolicyName=f'{function_name}-scaling-policy',
            ServiceNamespace='lambda',
            ResourceId=f'function:{function_name}:provisioned',
            ScalableDimension='lambda:function:ProvisionedConcurrency',
            PolicyType='TargetTrackingScaling',
            TargetTrackingScalingPolicyConfiguration={
                'TargetValue': 70.0,
                'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'LambdaProvisionedConcurrencyUtilization'
                }
            }
        )
```

This completes the Production Deployment guide. The comprehensive documentation now includes all major aspects of deploying and managing the GenAI MLOps system with Langfuse on AWS in production environments.
