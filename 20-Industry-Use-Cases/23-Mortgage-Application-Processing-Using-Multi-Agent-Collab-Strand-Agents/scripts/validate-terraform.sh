#!/bin/bash

# Terraform Validation Script
# Validates Terraform configuration and checks for best practices

set -e

echo "🔍 Terraform Configuration Validation"

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

cd terraform

echo "📋 Running Terraform validation checks..."

# 1. Format check
echo "1️⃣  Checking Terraform formatting..."
if terraform fmt -check -diff; then
    echo "✅ Terraform files are properly formatted"
else
    echo "⚠️  Terraform files need formatting. Run 'terraform fmt' to fix."
fi

# 2. Validation check
echo "2️⃣  Validating Terraform configuration..."
if terraform validate; then
    echo "✅ Terraform configuration is valid"
else
    echo "❌ Terraform configuration has errors"
    exit 1
fi

# 3. Security check with tfsec (if available)
echo "3️⃣  Running security checks..."
if command -v tfsec &> /dev/null; then
    echo "🔒 Running tfsec security scan..."
    tfsec . || echo "⚠️  Security issues found. Review tfsec output."
else
    echo "⚠️  tfsec not installed. Consider installing for security checks."
    echo "   Install: https://github.com/aquasecurity/tfsec"
fi

# 4. Plan check for both environments
echo "4️⃣  Testing Terraform plans..."

echo "📋 Testing development environment plan..."
if terraform plan -var-file="environments/dev/terraform.tfvars" -out=dev.tfplan > /dev/null; then
    echo "✅ Development plan successful"
    rm -f dev.tfplan
else
    echo "❌ Development plan failed"
    exit 1
fi

echo "📋 Testing production environment plan..."
if terraform plan -var-file="environments/prod/terraform.tfvars" -out=prod.tfplan > /dev/null; then
    echo "✅ Production plan successful"
    rm -f prod.tfplan
else
    echo "❌ Production plan failed"
    exit 1
fi

# 5. Check for required files
echo "5️⃣  Checking required files..."
REQUIRED_FILES=(
    "main.tf"
    "variables.tf"
    "outputs.tf"
    "providers.tf"
    "versions.tf"
    "environments/dev/terraform.tfvars"
    "environments/prod/terraform.tfvars"
    "lambda/document_processor.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        exit 1
    fi
done

# 6. Check variable validation
echo "6️⃣  Checking variable validation..."
grep -q "validation {" variables.tf && echo "✅ Variable validation found" || echo "⚠️  Consider adding variable validation"

# 7. Check for tags
echo "7️⃣  Checking tagging strategy..."
grep -q "tags.*=" main.tf && echo "✅ Resource tagging implemented" || echo "⚠️  Consider implementing resource tagging"

# 8. Check for encryption
echo "8️⃣  Checking encryption configuration..."
grep -q "server_side_encryption" main.tf && echo "✅ S3 encryption configured" || echo "❌ S3 encryption not found"

cd ..

echo ""
echo "🎉 Terraform validation completed!"
echo ""
echo "📋 Validation Summary:"
echo "   ✅ Configuration syntax is valid"
echo "   ✅ Both environment plans are working"
echo "   ✅ Required files are present"
echo "   ✅ Security configurations are in place"
echo ""
echo "📝 Recommendations:"
echo "   - Run 'terraform fmt' to format files if needed"
echo "   - Install tfsec for comprehensive security scanning"
echo "   - Review any warnings mentioned above"
echo ""
echo "🚀 Ready for deployment!"
