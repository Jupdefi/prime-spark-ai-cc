# Prime Spark AI - Terraform Infrastructure

This directory contains Terraform configurations for deploying Prime Spark AI infrastructure to AWS.

## Structure

```
terraform/
├── provider.tf              # AWS provider configuration
├── main.tf                  # Main infrastructure orchestration
├── variables.tf             # Variable definitions
├── outputs.tf               # Output definitions
├── modules/                 # Reusable Terraform modules
│   ├── vpc/                 # VPC with multi-AZ subnets
│   ├── eks/                 # EKS Kubernetes cluster
│   ├── rds/                 # PostgreSQL database
│   ├── elasticache/         # Redis cluster
│   └── s3/                  # S3 buckets
└── environments/            # Environment-specific configurations
    ├── staging.tfvars       # Staging environment
    └── production.tfvars    # Production environment
```

## Prerequisites

- Terraform >= 1.5.0
- AWS CLI configured with appropriate credentials
- AWS account with necessary permissions

## Quick Start

### Initialize Terraform

```bash
cd deployment/terraform
terraform init
```

### Plan Deployment

**Staging:**
```bash
terraform plan -var-file=environments/staging.tfvars \
  -var="rds_master_username=postgres" \
  -var="rds_master_password=YOUR_PASSWORD"
```

**Production:**
```bash
terraform plan -var-file=environments/production.tfvars \
  -var="rds_master_username=postgres" \
  -var="rds_master_password=YOUR_PASSWORD"
```

### Apply Configuration

**Staging:**
```bash
terraform apply -var-file=environments/staging.tfvars \
  -var="rds_master_username=postgres" \
  -var="rds_master_password=YOUR_PASSWORD"
```

**Production:**
```bash
terraform apply -var-file=environments/production.tfvars \
  -var="rds_master_username=postgres" \
  -var="rds_master_password=YOUR_PASSWORD"
```

## Infrastructure Components

### VPC Module
- Multi-AZ VPC with public, private, and database subnets
- NAT Gateways for private subnet internet access
- VPC Flow Logs for network monitoring
- VPC Endpoints for S3 and ECR (production)

### EKS Module
- Managed Kubernetes cluster (v1.28)
- Multiple node groups with auto-scaling
- OIDC provider for IRSA (IAM Roles for Service Accounts)
- Essential add-ons: VPC CNI, CoreDNS, kube-proxy, EBS CSI driver

### RDS Module
- PostgreSQL 15.4 with Multi-AZ deployment
- Automated backups and maintenance windows
- Performance Insights enabled
- Read replicas (production)
- CloudWatch alarms for monitoring

### ElastiCache Module
- Redis 7.0 cluster with automatic failover
- Multi-AZ deployment (production)
- Automated snapshots
- Parameter groups optimized for Prime Spark AI

### S3 Module
- Data and backup buckets with versioning
- Server-side encryption with KMS
- Lifecycle policies for cost optimization
- Cross-region replication (production)

## Environment Configurations

### Staging
- Single NAT Gateway (cost optimization)
- t3/t3.large instances
- 2 AZs
- 7-day backups
- Budget: $500/month

### Production
- Multi-AZ NAT Gateways (high availability)
- m6i/r6g/g5 instance families
- 3 AZs
- 30-day backups
- Read replicas
- Budget: $5000/month

## Security

- All data encrypted at rest using KMS
- Network isolation with security groups
- VPC Flow Logs enabled
- IAM roles following least privilege principle
- Secrets managed via AWS Secrets Manager (configure separately)

## State Management

For production use, configure remote state in `provider.tf`:

```hcl
backend "s3" {
  bucket         = "prime-spark-terraform-state"
  key            = "infrastructure/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

## Connecting to EKS

After deployment, configure kubectl:

```bash
aws eks update-kubeconfig --region us-east-1 --name prime-spark-eks-staging
```

## Outputs

After successful deployment, Terraform outputs include:
- VPC ID and subnet IDs
- EKS cluster endpoint and OIDC provider
- RDS connection endpoint
- Redis endpoints
- S3 bucket names
- KMS key ARN

## Cost Estimation

**Staging:** ~$500/month
- EKS: ~$200
- RDS: ~$150
- ElastiCache: ~$100
- Data transfer & misc: ~$50

**Production:** ~$5000/month
- EKS: ~$2500
- RDS: ~$1500
- ElastiCache: ~$700
- Data transfer & misc: ~$300

## Maintenance

### Upgrading Kubernetes
1. Update `eks_cluster_version` in tfvars
2. Run `terraform plan` to preview changes
3. Apply during maintenance window

### Scaling
- EKS node groups auto-scale based on metrics
- RDS storage auto-scales up to `max_allocated_storage`
- Adjust min/max nodes in tfvars as needed

## Disaster Recovery

Production environment includes:
- Multi-region VPC peering
- RDS automated backups (30 days)
- S3 cross-region replication
- EKS cluster in secondary region (manual failover)

## Troubleshooting

### Common Issues

**Issue:** Terraform state lock error
**Solution:** Check DynamoDB table or manually release lock

**Issue:** EKS nodes not joining cluster
**Solution:** Verify security group rules and IAM roles

**Issue:** RDS connection timeout
**Solution:** Check security group allows traffic from EKS subnets

## Support

For issues or questions, refer to:
- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Project Documentation](../../README.md)
