#

## Getting Started

### Deploy infrastructure

```sh
make terraform-apply
```

### Deploy Agent via AgentCore

```sh
agentcore configure --entrypoint main.py -er <IAM_ROLE_ARN>
```

```sh
agentcore launch --local
```