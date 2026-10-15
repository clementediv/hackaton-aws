"""CDK entry point: `npx cdk deploy --profile hackaton` from infra/."""

import aws_cdk as cdk
from proactivo_stack import ProactivoStack

app = cdk.App()
ProactivoStack(
    app,
    "ChileAtiendeProactivo",
    env=cdk.Environment(region="us-east-1"),
    description="Detección proactiva de beneficios: DynamoDB Streams, Lambda y SES (demo).",
)
app.synth()
