# API Reference - GenAI MLOps with Langfuse on AWS

## 🔌 Core API Functions

### Bedrock Converse API Wrapper

#### `converse(messages, model_id, prompt=None, metadata={}, **kwargs)`

**Purpose**: Main function for chat completions with Langfuse observability

**Parameters**:
- `messages` (List[Dict]): Conversation messages in OpenAI or Bedrock format
- `model_id` (str): Bedrock model identifier (default: "us.amazon.nova-pro-v1:0")
- `prompt` (PromptClient, optional): Langfuse prompt template
- `metadata` (Dict): Additional metadata for tracing
- `**kwargs`: Additional Bedrock parameters (inferenceConfig, guardrailConfig, etc.)

**Returns**: `str` - Generated response text

**Example**:
```python
from utils import converse

response = converse(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing"}
    ],
    model_id="us.amazon.nova-pro-v1:0",
    inferenceConfig={"maxTokens": 1000, "temperature": 0.7},
    metadata={"use_case": "educational", "topic": "quantum_computing"}
)
```

**Langfuse Tracing**:
- Automatically captures input/output
- Tracks token usage (input, output, total)
- Records model parameters
- Logs errors and performance metrics

---

#### `converse_tool_use(messages, tools, tool_choice="auto", model_id, **kwargs)`

**Purpose**: Function calling with tools and Langfuse observability

**Parameters**:
- `messages` (List[Dict]): Conversation messages
- `tools` (List[Dict]): Available tools in OpenAI format
- `tool_choice` (str): Tool selection strategy ("auto", "any", or specific tool name)
- `model_id` (str): Bedrock model identifier
- `**kwargs`: Additional Bedrock parameters

**Returns**: `List[Dict]` - Tool calls to execute

**Example**:
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }
]

tool_calls = converse_tool_use(
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto",
    model_id="us.amazon.nova-pro-v1:0"
)
```

---

### Utility Functions

#### `convert_to_bedrock_messages(messages)`

**Purpose**: Convert OpenAI format messages to Bedrock Converse API format

**Parameters**:
- `messages` (List[Dict]): Messages in OpenAI format

**Returns**: `Tuple[List[Dict], List[Dict]]` - (system_prompts, bedrock_messages)

**Supported Content Types**:
- Text messages
- Image messages (with URL download and encoding)
- Multi-modal conversations

**Example**:
```python
openai_messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": [
        {"type": "text", "text": "Describe this image:"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ]}
]

system_prompts, bedrock_messages = convert_to_bedrock_messages(openai_messages)
```

---

#### `get_secret()`

**Purpose**: Retrieve Langfuse credentials from AWS Secrets Manager

**Returns**: `str` - JSON string containing Langfuse credentials

**Configuration**:
- Secret Name: "LangFuse-LLM-monitoring"
- Region: "us-east-1"

**Example**:
```python
import json
secret_string = get_secret()
credentials = json.loads(secret_string)

langfuse_host = credentials["LANGFUSE_HOST"]
langfuse_secret_key = credentials["LANGFUSE_SECRET_KEY"]
langfuse_public_key = credentials["LANGFUSE_PUBLIC_KEY"]
```

---

## 🎛️ Configuration Objects

### MODEL_CONFIG

```python
MODEL_CONFIG = {
    "nova_pro": {
        "model_id": "us.amazon.nova-pro-v1:0",
        "inferenceConfig": {
            "maxTokens": 4096,
            "temperature": 0,
            "topP": 0.9,
            "stopSequences": []
        }
    },
    "nova_lite": {
        "model_id": "us.amazon.nova-lite-v1:0", 
        "inferenceConfig": {
            "maxTokens": 2048,
            "temperature": 0,
            "topP": 0.9
        }
    },
    "nova_micro": {
        "model_id": "us.amazon.nova-micro-v1:0",
        "inferenceConfig": {
            "maxTokens": 2048,
            "temperature": 0,
            "topP": 0.9
        }
    }
}
```

### GUARDRAIL_CONFIG

```python
GUARDRAIL_CONFIG = {
    "guardrailIdentifier": "arn:aws:bedrock:us-east-1:ACCOUNT:guardrail/ID",
    "guardrailVersion": "1",
    "trace": "enabled"
}
```

---

## 🏷️ Langfuse Decorators

### @observe Decorator

**Purpose**: Add observability to any function

**Parameters**:
- `as_type` (str): Observation type ("generation", "retrieval", "evaluation", "span")
- `name` (str): Display name in Langfuse dashboard
- `capture_input` (bool): Whether to capture function input (default: True)
- `capture_output` (bool): Whether to capture function output (default: True)

**Types**:

#### Generation
```python
@observe(as_type="generation", name="Custom Generation")
def my_generation_function(prompt):
    # Function implementation
    return response
```

#### Retrieval
```python
@observe(as_type="retrieval", name="Document Search")
def search_documents(query, top_k=5):
    # Retrieval implementation
    return documents
```

#### Evaluation
```python
@observe(as_type="evaluation", name="Quality Assessment")
def evaluate_response(input_text, output_text):
    # Evaluation logic
    return metrics
```

#### Span (General)
```python
@observe(as_type="span", name="Data Processing")
def process_data(data):
    # Processing logic
    return processed_data
```

---

## 🔄 Langfuse Context Management

### langfuse_context

**Purpose**: Update current observation with additional metadata

**Methods**:

#### `update_current_observation(**kwargs)`

```python
from langfuse.decorators import langfuse_context

langfuse_context.update_current_observation(
    input=input_data,
    output=output_data,
    model=model_id,
    model_parameters={"temperature": 0.7, "max_tokens": 1000},
    usage={"input": 150, "output": 300, "total": 450},
    metadata={"version": "1.0", "environment": "production"},
    level="INFO",  # or "WARNING", "ERROR"
    status_message="Operation completed successfully"
)
```

#### Common Parameters:
- `input`: Function input data
- `output`: Function output data  
- `model`: Model identifier
- `model_parameters`: Model configuration
- `usage`: Token usage statistics
- `metadata`: Additional context information
- `level`: Log level (INFO, WARNING, ERROR)
- `status_message`: Status description
- `prompt`: Associated prompt template

---

## 🛠️ Error Handling Patterns

### Standard Error Handling

```python
@observe(as_type="generation", name="Safe Generation")
def safe_generate(messages, **kwargs):
    try:
        response = bedrock_runtime.converse(
            messages=messages,
            **kwargs
        )
        
        # Update success metrics
        langfuse_context.update_current_observation(
            output=response["output"]["message"]["content"][0]["text"],
            usage={
                "input": response["usage"]["inputTokens"],
                "output": response["usage"]["outputTokens"],
                "total": response["usage"]["totalTokens"]
            },
            level="INFO",
            status_message="Generation successful"
        )
        
        return response["output"]["message"]["content"][0]["text"]
        
    except ClientError as e:
        error_message = f"AWS Client Error: {str(e)}"
        langfuse_context.update_current_observation(
            level="ERROR",
            status_message=error_message,
            metadata={"error_type": "ClientError", "error_code": e.response.get('Error', {}).get('Code')}
        )
        raise
        
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        langfuse_context.update_current_observation(
            level="ERROR", 
            status_message=error_message,
            metadata={"error_type": type(e).__name__}
        )
        raise
```

---

## 📊 Metrics and Monitoring

### Token Usage Tracking

```python
def track_token_usage(response):
    usage_metrics = {
        "input_tokens": response["usage"]["inputTokens"],
        "output_tokens": response["usage"]["outputTokens"], 
        "total_tokens": response["usage"]["totalTokens"],
        "cost_estimate": calculate_cost(response["usage"])
    }
    
    langfuse_context.update_current_observation(
        usage=usage_metrics,
        metadata={"cost_tracking": True}
    )
    
    return usage_metrics
```

### Performance Monitoring

```python
import time

@observe(as_type="span", name="Performance Monitoring")
def monitor_performance(func, *args, **kwargs):
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
        end_time = time.time()
        
        langfuse_context.update_current_observation(
            metadata={
                "execution_time": end_time - start_time,
                "status": "success"
            }
        )
        
        return result
        
    except Exception as e:
        end_time = time.time()
        
        langfuse_context.update_current_observation(
            level="ERROR",
            metadata={
                "execution_time": end_time - start_time,
                "status": "error",
                "error": str(e)
            }
        )
        raise
```

---

## 🔐 Security Best Practices

### Credential Management

```python
import boto3
import json
from botocore.exceptions import ClientError

def get_secure_credentials(secret_name, region_name="us-east-1"):
    """Securely retrieve credentials from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        raise
```

### Input Sanitization

```python
def sanitize_input(user_input):
    """Sanitize user input before processing"""
    # Remove potential injection patterns
    sanitized = user_input.strip()
    
    # Log sanitization for audit
    langfuse_context.update_current_observation(
        metadata={
            "input_sanitized": True,
            "original_length": len(user_input),
            "sanitized_length": len(sanitized)
        }
    )
    
    return sanitized
```

This completes the API Reference section. Would you like me to continue with the Best Practices, Troubleshooting, and Production Deployment sections?
