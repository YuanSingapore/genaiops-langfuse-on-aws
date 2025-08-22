# GenAI MLOps with Langfuse on AWS

## 🎯 Overview

This repository is based on the great work of AWS team (https://github.com/aws-samples/genai-ml-platform-examples/tree/main/integration) with minor changes on versioning and Langfuse integration. It provides a **comprehensive hands-on workshop** for implementing **GenAI MLOps using Langfuse** integrated with **AWS Bedrock**. It demonstrates production-ready patterns for LLM observability, monitoring, and operational excellence.

## 🚀 Quick Start

### Prerequisites
- AWS Account with Bedrock access
- Langfuse account for observability
- Python 3.8+ environment
- SageMaker Studio (recommended)

### Setup
```bash
# Clone repository
git clone https://github.com/YuanSingapore/genaiops-langfuse-on-aws.git
cd genaiops-langfuse-on-aws

# Install dependencies
pip install langfuse boto3 python-dotenv

# Configure AWS credentials
aws configure

# Set up Langfuse credentials in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "LangFuse-LLM-monitoring" \
    --secret-string '{"LANGFUSE_SECRET_KEY":"your-key","LANGFUSE_PUBLIC_KEY":"your-key","LANGFUSE_HOST":"https://your-instance.com"}'
```

## 📚 Documentation

### Core Documentation
- **[📖 Comprehensive Documentation](COMPREHENSIVE_DOCUMENTATION.md)** - Complete guide with architecture, setup, and lab walkthrough
- **[🔌 API Reference](API_REFERENCE.md)** - Detailed API documentation and code examples
- **[⚡ Best Practices & Troubleshooting](BEST_PRACTICES_TROUBLESHOOTING.md)** - Production best practices and common issue solutions
- **[🚀 Production Deployment](PRODUCTION_DEPLOYMENT.md)** - Infrastructure, CI/CD, monitoring, and scaling guide

## 🧪 Lab Structure

### Lab 1: Langfuse Basics
**Objective**: Introduction to Langfuse observability and basic tracing
- ✅ Langfuse SDK integration
- ✅ Basic tracing with `@observe` decorators
- ✅ Dashboard navigation and token monitoring

### Lab 2: RAG with Langfuse  
**Objective**: Build and monitor a complete RAG system
- ✅ Document ingestion and vectorization
- ✅ End-to-end pipeline monitoring
- ✅ Retrieval quality tracking

### Lab 3: Model Evaluation & Guardrails
**Objective**: Implement automated evaluation and content safety
- ✅ **Lab 3.1**: Model-based evaluation frameworks
- ✅ **Lab 3.2**: Bedrock Guardrails integration

### Lab 4: Advanced Integration (Strands MCP)
**Objective**: Advanced patterns with Model Context Protocol
- ✅ Multi-agent workflows
- ✅ Complex tool integration
- ✅ Production-scale orchestration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   AWS Bedrock   │───▶│    Langfuse     │
│   (Jupyter)     │    │   (Nova Models) │    │  (Observability)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Configuration  │    │   Guardrails    │    │   Monitoring    │
│   (config.py)   │    │   (Safety)      │    │   Dashboard     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Key Components

### Core Files
- **`config.py`** - Model configurations (Nova Pro, Lite, Micro)
- **`utils.py`** - Bedrock API wrappers with Langfuse integration
- **`lab1/`** - Langfuse basics and setup
- **`lab2/`** - RAG implementation with monitoring
- **`lab3/`** - Model evaluation and guardrails
- **`lab4/`** - Advanced MCP integration

### Model Configuration
```python
MODEL_CONFIG = {
    "nova_pro": {"model_id": "us.amazon.nova-pro-v1:0", "maxTokens": 4096},
    "nova_lite": {"model_id": "us.amazon.nova-lite-v1:0", "maxTokens": 2048},
    "nova_micro": {"model_id": "us.amazon.nova-micro-v1:0", "maxTokens": 2048}
}
```

## 💡 Key Features

- ✅ **Production-Ready**: Enterprise-grade observability patterns
- ✅ **Cost Optimization**: Token usage tracking and analysis
- ✅ **Quality Assurance**: Automated model evaluation frameworks
- ✅ **Compliance**: Content safety and comprehensive audit trails
- ✅ **Scalability**: Designed for high-volume production workloads
- ✅ **Multi-Modal**: Support for text and image processing
- ✅ **Error Handling**: Comprehensive error capture and recovery

## 🛠️ Usage Examples

### Basic Chat with Observability
```python
from utils import converse
from langfuse.decorators import observe

@observe(as_type="generation", name="Customer Support")
def customer_chat(message):
    return converse(
        messages=[{"role": "user", "content": message}],
        model_id="us.amazon.nova-lite-v1:0",
        metadata={"use_case": "customer_support"}
    )

response = customer_chat("How can I reset my password?")
```

### RAG with Monitoring
```python
@observe(as_type="retrieval", name="Document Search")
def search_documents(query):
    # Your retrieval logic here
    return relevant_docs

@observe(as_type="generation", name="RAG Response")
def rag_generate(query):
    docs = search_documents(query)
    context = "\n".join([doc.content for doc in docs])
    
    return converse(
        messages=[
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user", "content": query}
        ]
    )
```

## 🔐 Security & Compliance

- **AWS Secrets Manager**: Secure credential storage
- **Bedrock Guardrails**: Content safety and filtering
- **PII Detection**: Automatic masking of sensitive information
- **Input Validation**: Comprehensive request sanitization
- **Audit Trails**: Complete observability and logging

## 📊 Monitoring & Analytics

- **Real-time Tracing**: Complete request/response tracking
- **Token Usage Analytics**: Cost optimization insights
- **Performance Metrics**: Latency and throughput monitoring
- **Error Tracking**: Comprehensive error analysis
- **Custom Dashboards**: Langfuse observability platform

## 🚀 Production Deployment

The repository includes comprehensive production deployment guides:

- **Infrastructure as Code**: CloudFormation templates
- **CI/CD Pipelines**: GitHub Actions workflows
- **Auto Scaling**: Lambda concurrency management
- **Monitoring**: CloudWatch dashboards and alarms
- **Security**: WAF rules and hardening guidelines

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the comprehensive guides above
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and community support

## 🏷️ Tags

`aws` `bedrock` `langfuse` `mlops` `genai` `observability` `monitoring` `production` `rag` `guardrails`

