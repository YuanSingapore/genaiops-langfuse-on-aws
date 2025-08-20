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
    "guardrailIdentifier": "arn:aws:bedrock:us-east-1:369776982489:guardrail/uua0lb6pqiyq", # TODO: Fill the value using "GuardrailId" from the Event Outputs
    "guardrailVersion": "1",
    "trace": "enabled",
}