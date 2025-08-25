# Project Restructure Suggestion: Mortgage Application Processing Multi-Agent System

## Current Structure Analysis

### Issues Identified:
1. **Mixed concerns**: Scripts, source code, and infrastructure are intermixed
2. **Import inconsistencies**: Relative imports mixed with absolute imports
3. **No clear separation**: Business logic, utilities, and infrastructure not properly separated
4. **Missing standard files**: No proper setup.py, MANIFEST.in, or package configuration
5. **Duplicate utilities**: utils.py exists in both `src/` and `scripts/`
6. **No testing structure**: No dedicated test directories or test organization
7. **Configuration scattered**: Environment-specific configs not centralized

## Recommended New Structure

```
mortgage-application-processor/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .gitignore
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── cd.yml
│   │   └── security.yml
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── pyproject.toml                    # Modern Python packaging
├── setup.cfg                         # Additional configuration
├── requirements/
│   ├── base.txt                      # Core dependencies
│   ├── dev.txt                       # Development dependencies
│   ├── test.txt                      # Testing dependencies
│   └── prod.txt                      # Production dependencies
├── src/
│   └── mortgage_processor/           # Main package (importable)
│       ├── __init__.py
│       ├── core/                     # Core business logic
│       │   ├── __init__.py
│       │   ├── agents/
│       │   │   ├── __init__.py
│       │   │   ├── base.py           # Base agent class
│       │   │   ├── data_extraction.py
│       │   │   ├── validation.py
│       │   │   └── storage.py
│       │   ├── models/               # Data models
│       │   │   ├── __init__.py
│       │   │   ├── mortgage.py
│       │   │   └── validation.py
│       │   └── workflows/            # Multi-agent workflows
│       │       ├── __init__.py
│       │       └── processing.py
│       ├── infrastructure/           # AWS/Infrastructure code
│       │   ├── __init__.py
│       │   ├── aws/
│       │   │   ├── __init__.py
│       │   │   ├── bedrock.py
│       │   │   ├── dynamodb.py
│       │   │   ├── s3.py
│       │   │   └── lambda_handler.py
│       │   └── mcp/                  # MCP client configurations
│       │       ├── __init__.py
│       │       └── clients.py
│       ├── utils/                    # Shared utilities
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   ├── config.py
│       │   ├── exceptions.py
│       │   └── helpers.py
│       └── cli/                      # Command line interface
│           ├── __init__.py
│           └── main.py
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_agents/
│   │   │   ├── __init__.py
│   │   │   ├── test_data_extraction.py
│   │   │   ├── test_validation.py
│   │   │   └── test_storage.py
│   │   ├── test_models/
│   │   │   ├── __init__.py
│   │   │   └── test_mortgage.py
│   │   └── test_utils/
│   │       ├── __init__.py
│   │       └── test_helpers.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_workflows.py
│   │   └── test_aws_integration.py
│   └── fixtures/                     # Test data
│       ├── sample_documents/
│       └── mock_responses/
├── docs/                             # Documentation
│   ├── index.md
│   ├── api/
│   ├── guides/
│   │   ├── getting-started.md
│   │   ├── deployment.md
│   │   └── configuration.md
│   └── architecture/
│       ├── overview.md
│       └── diagrams/
├── scripts/                          # Deployment and utility scripts
│   ├── setup/
│   │   ├── __init__.py
│   │   ├── aws_setup.py
│   │   └── cognito_setup.py
│   ├── deployment/
│   │   ├── __init__.py
│   │   └── deploy.py
│   └── utilities/
│       ├── __init__.py
│       └── bda_project.py
├── infrastructure/                   # Infrastructure as Code
│   ├── terraform/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   ├── modules/
│   │   │   ├── lambda/
│   │   │   ├── dynamodb/
│   │   │   ├── s3/
│   │   │   └── api-gateway/
│   │   └── shared/
│   └── docker/
│       ├── Dockerfile
│       ├── docker-compose.yml
│       └── docker-compose.dev.yml
├── config/                           # Configuration files
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── staging.py
│   │   └── production.py
│   └── logging/
│       ├── development.yaml
│       └── production.yaml
└── examples/                         # Usage examples
    ├── basic_usage.py
    ├── custom_agents.py
    └── notebooks/
        └── mortgage_processing_demo.ipynb
```

## Key Improvements

### 1. Package Structure
- **Proper Python package**: `src/mortgage_processor/` as the main importable package
- **Clear separation**: Core logic, infrastructure, utilities, and CLI separated
- **Namespace packages**: Organized by functionality rather than file type

### 2. Import Strategy
```python
# Absolute imports from package root
from mortgage_processor.core.agents import DataExtractionAgent
from mortgage_processor.infrastructure.aws import BedrockClient
from mortgage_processor.utils.config import get_settings

# Clear module boundaries
from mortgage_processor.core.models.mortgage import MortgageApplication
```

### 3. Configuration Management
```python
# config/settings/base.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    dynamodb_table_name: str = "mortgage-applications"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### 4. Modern Python Packaging (pyproject.toml)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mortgage-processor"
version = "0.1.0"
description = "Multi-agent mortgage application processing system"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial Services",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "boto3>=1.39.0",
    "pydantic>=2.11.0",
    "strands-agents",
    "bedrock-agentcore",
    "fastmcp>=2.10.0",
    "httpx>=0.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.10.0",
    "moto>=4.2.0",  # AWS mocking
]

[project.scripts]
mortgage-processor = "mortgage_processor.cli.main:main"

[project.urls]
Homepage = "https://github.com/yourusername/mortgage-processor"
Documentation = "https://mortgage-processor.readthedocs.io"
Repository = "https://github.com/yourusername/mortgage-processor"
Issues = "https://github.com/yourusername/mortgage-processor/issues"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
src_paths = ["src", "tests"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"
```

### 5. Base Agent Class
```python
# src/mortgage_processor/core/agents/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from strands import Agent
from strands.models import BedrockModel
from mortgage_processor.utils.config import get_settings

class BaseAgent(ABC):
    """Base class for all mortgage processing agents."""
    
    def __init__(self, model_id: Optional[str] = None):
        self.settings = get_settings()
        self.model = BedrockModel(
            model_id=model_id or self.settings.bedrock_model_id,
            region=self.settings.aws_region
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self.get_system_prompt()
        )
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return results."""
        pass
```

### 6. Testing Structure
```python
# tests/conftest.py
import pytest
from moto import mock_dynamodb, mock_s3, mock_bedrock
from mortgage_processor.utils.config import get_settings

@pytest.fixture
def settings():
    return get_settings()

@pytest.fixture
def mock_aws():
    with mock_dynamodb(), mock_s3(), mock_bedrock():
        yield

# tests/unit/test_agents/test_data_extraction.py
import pytest
from mortgage_processor.core.agents.data_extraction import DataExtractionAgent

class TestDataExtractionAgent:
    @pytest.fixture
    def agent(self):
        return DataExtractionAgent()
    
    async def test_process_document(self, agent, mock_aws):
        # Test implementation
        pass
```

### 7. CLI Interface
```python
# src/mortgage_processor/cli/main.py
import click
from mortgage_processor.core.workflows.processing import MortgageProcessingWorkflow

@click.group()
def cli():
    """Mortgage Application Processing CLI."""
    pass

@cli.command()
@click.option('--document-path', required=True, help='Path to mortgage document')
@click.option('--output-format', default='json', help='Output format')
def process(document_path: str, output_format: str):
    """Process a mortgage application document."""
    workflow = MortgageProcessingWorkflow()
    result = workflow.process_document(document_path)
    click.echo(f"Processing complete: {result}")

if __name__ == '__main__':
    cli()
```

## Migration Steps

1. **Create new structure**: Set up the recommended directory structure
2. **Move and refactor code**: 
   - Move agents to `src/mortgage_processor/core/agents/`
   - Create base classes and proper inheritance
   - Separate AWS infrastructure code
3. **Update imports**: Convert to absolute imports using the new package structure
4. **Add configuration management**: Centralize settings using Pydantic
5. **Create proper packaging**: Add pyproject.toml and setup.cfg
6. **Add comprehensive tests**: Unit, integration, and end-to-end tests
7. **Documentation**: Add proper documentation structure
8. **CI/CD**: Set up GitHub Actions for testing and deployment

## Benefits of This Structure

1. **Maintainability**: Clear separation of concerns and modular design
2. **Testability**: Comprehensive test structure with proper mocking
3. **Scalability**: Easy to add new agents and workflows
4. **Professional**: Follows Python packaging best practices
5. **Deployment**: Separated infrastructure code for different environments
6. **Documentation**: Proper documentation structure for open-source projects
7. **Development**: Better developer experience with proper tooling setup

This structure transforms your project from a prototype into a production-ready, open-source quality codebase that follows industry best practices.
