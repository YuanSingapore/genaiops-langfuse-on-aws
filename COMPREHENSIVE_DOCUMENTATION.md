# GenAI MLOps with Langfuse on AWS - Comprehensive Documentation

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites & Setup](#prerequisites--setup)
4. [Lab Walkthrough](#lab-walkthrough)
5. [Configuration Guide](#configuration-guide)
6. [API Reference](#api-reference)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)
10. [Appendices](#appendices)

---

## 🎯 Executive Summary

This repository provides a **comprehensive hands-on workshop** for implementing **GenAI MLOps using Langfuse** integrated with **AWS Bedrock**. It demonstrates production-ready patterns for:

- **LLM Observability**: Complete tracing and monitoring of AI model interactions
- **RAG Pipeline Monitoring**: End-to-end observability for Retrieval-Augmented Generation
- **Model Evaluation**: Automated assessment and quality assurance
- **Content Safety**: Bedrock Guardrails integration with monitoring
- **Advanced Integrations**: Model Context Protocol (MCP) and complex workflow tracking

### Key Benefits

- ✅ **Production-Ready**: Enterprise-grade observability patterns
- ✅ **Cost Optimization**: Token usage tracking and analysis
- ✅ **Quality Assurance**: Automated model evaluation frameworks
- ✅ **Compliance**: Content safety and comprehensive audit trails
- ✅ **Scalability**: Designed for high-volume production workloads

---

## 🏗️ Architecture Overview

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   AWS Bedrock   │───▶│    Langfuse     │
│   (Jupyter)     │    │   (Nova Models) │    │  (Observability)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Configuration  │    │   Guardrails    │    │   Monitoring    │
│   (config.py)   │    │   (Safety)      │    │   Dashboard     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **AWS Bedrock Foundation Models**
   - Nova Pro (4K tokens): High-performance model for complex tasks
   - Nova Lite (2K tokens): Balanced performance and cost
   - Nova Micro (2K tokens): Cost-optimized for simple tasks

2. **Langfuse Observability Platform**
   - Real-time tracing and monitoring
   - Token usage analytics
   - Performance metrics
   - Error tracking and debugging

3. **Bedrock Guardrails**
   - Content filtering and safety
   - Compliance monitoring
   - Risk mitigation

4. **AWS Secrets Manager**
   - Secure credential storage
   - Automated secret rotation
   - Access control

### Data Flow

```
User Request → Message Conversion → Bedrock API → Langfuse Tracing → Response
     ↓              ↓                    ↓              ↓             ↓
Configuration → Format Validation → Model Inference → Observability → User
```

---

## 🔧 Prerequisites & Setup

### System Requirements

- **Python**: 3.8 or higher
- **AWS Account**: With Bedrock access enabled
- **Langfuse Account**: For observability dashboard
- **SageMaker Studio**: Recommended environment
- **IAM Permissions**: Bedrock, Secrets Manager, S3 access

### AWS Services Setup

#### 1. Enable AWS Bedrock Models

```bash
# Check available models
aws bedrock list-foundation-models --region us-east-1

# Request model access (if needed)
aws bedrock put-model-invocation-logging-configuration \
    --logging-config '{"cloudWatchConfig":{"logGroupName":"bedrock-model-invocation-logs","roleArn":"arn:aws:iam::ACCOUNT:role/service-role/AmazonBedrockExecutionRoleForCloudWatchLogs"}}'
```

#### 2. Configure Secrets Manager

```bash
# Create Langfuse credentials secret
aws secretsmanager create-secret \
    --name "LangFuse-LLM-monitoring" \
    --description "Langfuse API credentials for LLM monitoring" \
    --secret-string '{"LANGFUSE_SECRET_KEY":"your-secret-key","LANGFUSE_PUBLIC_KEY":"your-public-key","LANGFUSE_HOST":"https://your-langfuse-instance.com"}'
```

#### 3. Setup Bedrock Guardrails

```bash
# Create guardrail (example)
aws bedrock create-guardrail \
    --name "content-safety-guardrail" \
    --description "Content safety and compliance guardrail" \
    --content-policy-config file://guardrail-config.json
```

### Environment Setup

#### 1. Clone Repository

```bash
git clone https://github.com/YuanSingapore/genaiops-langfuse-on-aws.git
cd genaiops-langfuse-on-aws
```

#### 2. Install Dependencies

```bash
# For Lab 1-3
pip install langfuse boto3 python-dotenv

# For Lab 4 (Advanced)
pip install -r lab4/requirements.txt
```

#### 3. Configure Environment Variables

```bash
# Create .env file
cat > .env << EOF
AWS_REGION=us-east-1
LANGFUSE_SECRET_NAME=LangFuse-LLM-monitoring
GUARDRAIL_ID=your-guardrail-id
EOF
```

---

## 🧪 Lab Walkthrough

### Lab 1: Langfuse Basics

**Objective**: Introduction to Langfuse observability and basic tracing

**Key Concepts**:
- Langfuse SDK integration
- Basic tracing with `@observe` decorators
- Dashboard navigation
- Token usage monitoring

**What You'll Learn**:
```python
from langfuse.decorators import observe, langfuse_context

@observe(as_type="generation", name="Basic Chat")
def simple_chat(message, model_id="us.amazon.nova-lite-v1:0"):
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": message}]}]
    )
    return response["output"]["message"]["content"][0]["text"]
```

**Outcomes**:
- ✅ Understand Langfuse tracing fundamentals
- ✅ Set up basic observability pipeline
- ✅ Navigate Langfuse dashboard
- ✅ Monitor token usage and costs

### Lab 2: RAG with Langfuse

**Objective**: Build and monitor a complete RAG (Retrieval-Augmented Generation) system

**Key Components**:
- Document ingestion and vectorization
- Retrieval system with observability
- Generation with context tracking
- End-to-end pipeline monitoring

**Architecture**:
```
Documents → Embedding → Vector Store → Retrieval → Generation → Response
    ↓           ↓           ↓           ↓           ↓          ↓
 Langfuse   Langfuse   Langfuse   Langfuse   Langfuse   Langfuse
```

**Sample Implementation**:
```python
@observe(as_type="retrieval", name="Document Retrieval")
def retrieve_documents(query, top_k=5):
    # Vector similarity search
    results = vector_store.similarity_search(query, k=top_k)
    langfuse_context.update_current_observation(
        input=query,
        output=results,
        metadata={"top_k": top_k, "retrieval_method": "similarity"}
    )
    return results

@observe(as_type="generation", name="RAG Generation")
def generate_with_context(query, context_docs):
    # Combine query with retrieved context
    context = "\n".join([doc.page_content for doc in context_docs])
    messages = [
        {"role": "system", "content": f"Context: {context}"},
        {"role": "user", "content": query}
    ]
    return converse(messages)
```

**Outcomes**:
- ✅ Build production-ready RAG pipeline
- ✅ Monitor retrieval quality and relevance
- ✅ Track generation performance
- ✅ Optimize context window usage

### Lab 3: Model Evaluation & Guardrails

**Objective**: Implement automated model evaluation and content safety

#### Lab 3.1: Model-Based Evaluation

**Key Features**:
- Automated evaluation frameworks
- Quality metrics and scoring
- A/B testing capabilities
- Performance benchmarking

**Evaluation Metrics**:
```python
@observe(as_type="evaluation", name="Model Evaluation")
def evaluate_response(query, response, ground_truth=None):
    metrics = {
        "relevance": calculate_relevance(query, response),
        "coherence": calculate_coherence(response),
        "factuality": calculate_factuality(response, ground_truth),
        "safety": check_safety(response)
    }
    
    langfuse_context.update_current_observation(
        input={"query": query, "response": response},
        output=metrics,
        metadata={"evaluation_framework": "custom"}
    )
    return metrics
```

#### Lab 3.2: Bedrock Guardrails

**Safety Implementation**:
```python
from config import GUARDRAIL_CONFIG

@observe(as_type="generation", name="Guardrail Protected Generation")
def safe_generate(messages, **kwargs):
    return converse(
        messages=messages,
        guardrailConfig=GUARDRAIL_CONFIG,
        **kwargs
    )
```

**Outcomes**:
- ✅ Implement automated evaluation pipelines
- ✅ Set up content safety guardrails
- ✅ Monitor compliance and safety metrics
- ✅ Create quality assurance workflows

### Lab 4: Advanced Integration (Strands MCP)

**Objective**: Advanced integration patterns with Model Context Protocol

**Key Technologies**:
- Strands Agents framework
- Model Context Protocol (MCP)
- OpenTelemetry integration
- Advanced workflow orchestration

**Dependencies**:
```
strands-agents[otel]>=0.1.6
strands-agents-tools>=0.1.1
mcp>=0.1.0
awslabs-aws-documentation-mcp-server>=0.1.4
opentelemetry-exporter-otlp>=1.22.0
```

**Advanced Patterns**:
- Multi-agent workflows
- Complex tool integration
- Distributed tracing
- Production-scale orchestration

**Outcomes**:
- ✅ Implement advanced agent workflows
- ✅ Integrate MCP for enhanced context
- ✅ Set up distributed tracing
- ✅ Build production-scale systems

---

## ⚙️ Configuration Guide

### Core Configuration Files

#### config.py
```python
MODEL_CONFIG = {
    "nova_pro": {
        "model_id": "us.amazon.nova-pro-v1:0",
        "inferenceConfig": {"maxTokens": 4096, "temperature": 0},
    },
    "nova_lite": {
        "model_id": "us.amazon.nova-lite-v1:0", 
        "inferenceConfig": {"maxTokens": 2048, "temperature": 0},
    },
    "nova_micro": {
        "model_id": "us.amazon.nova-micro-v1:0",
        "inferenceConfig": {"maxTokens": 2048, "temperature": 0},
    },
}

GUARDRAIL_CONFIG = {
    "guardrailIdentifier": "arn:aws:bedrock:us-east-1:ACCOUNT:guardrail/ID",
    "guardrailVersion": "1",
    "trace": "enabled",
}
```

### Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=your-profile

# Langfuse Configuration  
LANGFUSE_SECRET_NAME=LangFuse-LLM-monitoring
LANGFUSE_HOST=https://your-instance.langfuse.com

# Model Configuration
DEFAULT_MODEL_ID=us.amazon.nova-lite-v1:0
MAX_TOKENS=2048
TEMPERATURE=0

# Guardrails
GUARDRAIL_ID=your-guardrail-id
GUARDRAIL_VERSION=1
```

### Secrets Manager Configuration

```json
{
  "LANGFUSE_SECRET_KEY": "sk-lf-...",
  "LANGFUSE_PUBLIC_KEY": "pk-lf-...", 
  "LANGFUSE_HOST": "https://your-instance.langfuse.com"
}
```

---

This is the first part of the comprehensive documentation. Would you like me to continue with the remaining sections (API Reference, Best Practices, Troubleshooting, etc.)?
