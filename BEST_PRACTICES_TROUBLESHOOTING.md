# Best Practices & Troubleshooting Guide

## 🎯 Best Practices

### 1. Observability Strategy

#### Comprehensive Tracing
```python
# ✅ Good: Comprehensive tracing with context
@observe(as_type="span", name="User Request Processing")
def process_user_request(user_id, request_data):
    langfuse_context.update_current_observation(
        metadata={
            "user_id": user_id,
            "request_type": request_data.get("type"),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    # Process request with nested observations
    validated_data = validate_input(request_data)
    response = generate_response(validated_data)
    
    return response

# ❌ Avoid: Minimal tracing without context
@observe()
def process_request(data):
    return generate_response(data)
```

#### Structured Metadata
```python
# ✅ Good: Structured, searchable metadata
metadata = {
    "environment": "production",
    "version": "1.2.3",
    "model_family": "nova",
    "use_case": "customer_support",
    "user_tier": "premium",
    "request_id": str(uuid.uuid4())
}

# ❌ Avoid: Unstructured or missing metadata
metadata = {"info": "some request"}
```

### 2. Error Handling & Resilience

#### Graceful Degradation
```python
@observe(as_type="generation", name="Resilient Generation")
def resilient_generate(messages, fallback_model=None):
    primary_model = "us.amazon.nova-pro-v1:0"
    fallback_model = fallback_model or "us.amazon.nova-lite-v1:0"
    
    try:
        return converse(messages, model_id=primary_model)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ThrottlingException':
            langfuse_context.update_current_observation(
                level="WARNING",
                status_message=f"Primary model throttled, using fallback: {fallback_model}"
            )
            return converse(messages, model_id=fallback_model)
        raise
```

#### Retry Logic with Exponential Backoff
```python
import time
import random
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    if e.response['Error']['Code'] in ['ThrottlingException', 'ServiceUnavailable']:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        langfuse_context.update_current_observation(
                            level="WARNING",
                            metadata={
                                "retry_attempt": attempt + 1,
                                "delay_seconds": delay,
                                "error_code": e.response['Error']['Code']
                            }
                        )
                        time.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
@observe(as_type="generation", name="Robust Generation")
def robust_generate(messages, **kwargs):
    return converse(messages, **kwargs)
```

### 3. Performance Optimization

#### Token Usage Optimization
```python
def optimize_token_usage(messages, max_context_tokens=3000):
    """Optimize token usage by truncating context if needed"""
    
    # Estimate token count (rough approximation: 1 token ≈ 4 characters)
    total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
    estimated_tokens = total_chars // 4
    
    if estimated_tokens > max_context_tokens:
        # Keep system message and recent user messages
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        
        # Truncate to fit within token limit
        truncated_messages = system_messages + user_messages[-2:]  # Keep last 2 user messages
        
        langfuse_context.update_current_observation(
            metadata={
                "token_optimization": True,
                "original_estimated_tokens": estimated_tokens,
                "truncated_messages": len(messages) - len(truncated_messages)
            }
        )
        
        return truncated_messages
    
    return messages
```

#### Caching Strategy
```python
import hashlib
import json
from functools import lru_cache

class ResponseCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
    
    def get_cache_key(self, messages, model_id, **kwargs):
        """Generate cache key from request parameters"""
        cache_data = {
            "messages": messages,
            "model_id": model_id,
            "kwargs": {k: v for k, v in kwargs.items() if k != "metadata"}
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, cache_key):
        return self.cache.get(cache_key)
    
    def set(self, cache_key, value):
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[cache_key] = value

response_cache = ResponseCache()

@observe(as_type="generation", name="Cached Generation")
def cached_generate(messages, model_id, **kwargs):
    cache_key = response_cache.get_cache_key(messages, model_id, **kwargs)
    
    # Check cache first
    cached_response = response_cache.get(cache_key)
    if cached_response:
        langfuse_context.update_current_observation(
            output=cached_response,
            metadata={"cache_hit": True, "cache_key": cache_key}
        )
        return cached_response
    
    # Generate new response
    response = converse(messages, model_id=model_id, **kwargs)
    
    # Cache the response
    response_cache.set(cache_key, response)
    
    langfuse_context.update_current_observation(
        metadata={"cache_hit": False, "cache_key": cache_key}
    )
    
    return response
```

### 4. Security Best Practices

#### Input Validation
```python
import re
from typing import List, Dict, Any

def validate_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate and sanitize input messages"""
    
    validated_messages = []
    
    for msg in messages:
        # Validate required fields
        if "role" not in msg or "content" not in msg:
            raise ValueError("Message must have 'role' and 'content' fields")
        
        # Validate role
        if msg["role"] not in ["system", "user", "assistant"]:
            raise ValueError(f"Invalid role: {msg['role']}")
        
        # Sanitize content
        content = msg["content"]
        if isinstance(content, str):
            # Remove potential injection patterns
            content = re.sub(r'<script.*?</script>', '', content, flags=re.IGNORECASE)
            content = content.strip()
        
        validated_messages.append({
            "role": msg["role"],
            "content": content
        })
    
    langfuse_context.update_current_observation(
        metadata={
            "input_validation": True,
            "original_message_count": len(messages),
            "validated_message_count": len(validated_messages)
        }
    )
    
    return validated_messages
```

#### PII Detection and Masking
```python
import re

def mask_pii(text: str) -> str:
    """Mask personally identifiable information"""
    
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Phone numbers (US format)
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\(\d{3}\)\s*\d{3}-\d{4}\b', '[PHONE]', text)
    
    # Social Security Numbers
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    
    # Credit Card Numbers (basic pattern)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CREDIT_CARD]', text)
    
    return text

@observe(as_type="span", name="PII Protection")
def protect_pii(messages):
    """Apply PII protection to messages"""
    protected_messages = []
    
    for msg in messages:
        if isinstance(msg.get("content"), str):
            original_content = msg["content"]
            protected_content = mask_pii(original_content)
            
            protected_messages.append({
                **msg,
                "content": protected_content
            })
            
            # Log PII detection (without exposing actual PII)
            pii_detected = original_content != protected_content
            langfuse_context.update_current_observation(
                metadata={
                    "pii_detected": pii_detected,
                    "content_length": len(original_content)
                }
            )
        else:
            protected_messages.append(msg)
    
    return protected_messages
```

### 5. Cost Management

#### Token Usage Monitoring
```python
class TokenUsageTracker:
    def __init__(self):
        self.usage_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_requests": 0,
            "cost_estimate": 0.0
        }
    
    def track_usage(self, usage_data, model_id):
        """Track token usage and estimate costs"""
        
        # Model pricing (example rates per 1K tokens)
        pricing = {
            "us.amazon.nova-pro-v1:0": {"input": 0.0008, "output": 0.0032},
            "us.amazon.nova-lite-v1:0": {"input": 0.0006, "output": 0.0024},
            "us.amazon.nova-micro-v1:0": {"input": 0.000035, "output": 0.00014}
        }
        
        input_tokens = usage_data.get("input", 0)
        output_tokens = usage_data.get("output", 0)
        
        # Calculate cost
        model_pricing = pricing.get(model_id, {"input": 0.001, "output": 0.004})
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        total_cost = input_cost + output_cost
        
        # Update stats
        self.usage_stats["total_input_tokens"] += input_tokens
        self.usage_stats["total_output_tokens"] += output_tokens
        self.usage_stats["total_requests"] += 1
        self.usage_stats["cost_estimate"] += total_cost
        
        return {
            "request_cost": total_cost,
            "cumulative_cost": self.usage_stats["cost_estimate"],
            "total_requests": self.usage_stats["total_requests"]
        }

usage_tracker = TokenUsageTracker()

@observe(as_type="generation", name="Cost-Aware Generation")
def cost_aware_generate(messages, model_id, **kwargs):
    response = converse(messages, model_id=model_id, **kwargs)
    
    # Track usage and costs
    if hasattr(langfuse_context, '_current_observation'):
        usage_data = langfuse_context._current_observation.usage
        if usage_data:
            cost_info = usage_tracker.track_usage(usage_data, model_id)
            
            langfuse_context.update_current_observation(
                metadata={
                    **cost_info,
                    "cost_tracking": True
                }
            )
    
    return response
```

---

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Authentication Issues

**Problem**: `403 Forbidden` or `InvalidSignatureException`

**Solutions**:
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Check IAM permissions
aws iam get-user-policy --user-name your-username --policy-name BedrockAccess
```

**Required IAM Permissions**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:LangFuse-LLM-monitoring*"
        }
    ]
}
```

#### 2. Model Access Issues

**Problem**: `AccessDeniedException` when invoking models

**Solution**:
```python
# Check model availability
import boto3

bedrock = boto3.client('bedrock', region_name='us-east-1')
models = bedrock.list_foundation_models()

available_models = [
    model['modelId'] for model in models['modelSummaries'] 
    if model['modelLifecycle']['status'] == 'ACTIVE'
]

print("Available models:", available_models)
```

**Enable Model Access**:
1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Request access for required models
4. Wait for approval (usually immediate for most models)

#### 3. Langfuse Connection Issues

**Problem**: Langfuse traces not appearing in dashboard

**Diagnostic Steps**:
```python
# Test Langfuse connection
import json
from langfuse import Langfuse

# Get credentials
secret = get_secret()
credentials = json.loads(secret)

# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=credentials["LANGFUSE_SECRET_KEY"],
    public_key=credentials["LANGFUSE_PUBLIC_KEY"],
    host=credentials["LANGFUSE_HOST"]
)

# Test connection
try:
    # Create a test trace
    trace = langfuse.trace(name="connection_test")
    trace.generation(
        name="test_generation",
        input="test input",
        output="test output"
    )
    
    # Flush to ensure data is sent
    langfuse.flush()
    print("✅ Langfuse connection successful")
    
except Exception as e:
    print(f"❌ Langfuse connection failed: {e}")
```

**Common Solutions**:
- Verify Langfuse host URL (should include https://)
- Check API keys are correct and not expired
- Ensure network connectivity from SageMaker to Langfuse
- Verify Langfuse project settings

#### 4. Token Limit Exceeded

**Problem**: `ValidationException` - Input is too long

**Solution**:
```python
def handle_token_limit(messages, model_id, max_retries=3):
    """Handle token limit by progressively reducing context"""
    
    for attempt in range(max_retries):
        try:
            return converse(messages, model_id=model_id)
            
        except ClientError as e:
            if "too long" in str(e).lower() or "token" in str(e).lower():
                if attempt == max_retries - 1:
                    raise
                
                # Reduce context size
                if len(messages) > 2:
                    # Keep system message and last user message
                    system_msgs = [msg for msg in messages if msg.get("role") == "system"]
                    user_msgs = [msg for msg in messages if msg.get("role") == "user"]
                    messages = system_msgs + user_msgs[-1:]
                    
                    langfuse_context.update_current_observation(
                        level="WARNING",
                        metadata={
                            "token_limit_retry": attempt + 1,
                            "reduced_context": True
                        }
                    )
                else:
                    # Truncate content if messages can't be reduced further
                    for msg in messages:
                        if isinstance(msg.get("content"), str) and len(msg["content"]) > 1000:
                            msg["content"] = msg["content"][:1000] + "..."
            else:
                raise
    
    return None
```

#### 5. Guardrails Issues

**Problem**: Content blocked by guardrails

**Diagnostic**:
```python
@observe(as_type="generation", name="Guardrail Diagnostic")
def diagnose_guardrail_issue(messages, **kwargs):
    try:
        # Try without guardrails first
        response_no_guardrail = converse(messages, **kwargs)
        
        # Try with guardrails
        response_with_guardrail = converse(
            messages, 
            guardrailConfig=GUARDRAIL_CONFIG,
            **kwargs
        )
        
        return response_with_guardrail
        
    except ClientError as e:
        if "guardrail" in str(e).lower():
            langfuse_context.update_current_observation(
                level="WARNING",
                status_message=f"Content blocked by guardrail: {str(e)}",
                metadata={
                    "guardrail_blocked": True,
                    "guardrail_id": GUARDRAIL_CONFIG.get("guardrailIdentifier")
                }
            )
            
            # Return sanitized response or error message
            return "I cannot provide a response to that request due to content policy restrictions."
        raise
```

#### 6. Performance Issues

**Problem**: Slow response times

**Diagnostic Tools**:
```python
import time
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Log performance metrics
            langfuse_context.update_current_observation(
                metadata={
                    "execution_time_seconds": execution_time,
                    "performance_status": "normal" if execution_time < 5 else "slow"
                }
            )
            
            if execution_time > 10:
                print(f"⚠️  Slow execution detected: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            langfuse_context.update_current_observation(
                level="ERROR",
                metadata={
                    "execution_time_seconds": end_time - start_time,
                    "error": str(e)
                }
            )
            raise
    
    return wrapper

@performance_monitor
@observe(as_type="generation", name="Monitored Generation")
def monitored_generate(messages, **kwargs):
    return converse(messages, **kwargs)
```

### Debug Mode

**Enable Debug Logging**:
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@observe(as_type="span", name="Debug Session")
def debug_generate(messages, **kwargs):
    logger.debug(f"Input messages: {messages}")
    logger.debug(f"Model parameters: {kwargs}")
    
    try:
        response = converse(messages, **kwargs)
        logger.debug(f"Response: {response}")
        return response
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise
```

### Health Check Function

```python
def health_check():
    """Comprehensive health check for the system"""
    
    health_status = {
        "aws_credentials": False,
        "bedrock_access": False,
        "langfuse_connection": False,
        "secrets_manager": False,
        "overall_status": "unhealthy"
    }
    
    try:
        # Check AWS credentials
        sts = boto3.client('sts')
        sts.get_caller_identity()
        health_status["aws_credentials"] = True
        
        # Check Bedrock access
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        bedrock.list_foundation_models()
        health_status["bedrock_access"] = True
        
        # Check Secrets Manager
        secret = get_secret()
        health_status["secrets_manager"] = True
        
        # Check Langfuse connection
        credentials = json.loads(secret)
        langfuse = Langfuse(
            secret_key=credentials["LANGFUSE_SECRET_KEY"],
            public_key=credentials["LANGFUSE_PUBLIC_KEY"],
            host=credentials["LANGFUSE_HOST"]
        )
        
        # Test trace creation
        trace = langfuse.trace(name="health_check")
        langfuse.flush()
        health_status["langfuse_connection"] = True
        
        # Overall status
        if all(health_status[key] for key in health_status if key != "overall_status"):
            health_status["overall_status"] = "healthy"
        
    except Exception as e:
        print(f"Health check failed: {e}")
    
    return health_status

# Run health check
if __name__ == "__main__":
    status = health_check()
    print(json.dumps(status, indent=2))
```

This completes the Best Practices and Troubleshooting guide. Would you like me to create the final section covering Production Deployment and additional resources?
