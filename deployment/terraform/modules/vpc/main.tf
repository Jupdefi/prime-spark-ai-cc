# VPC Module - Multi-AZ Network Infrastructure
# Creates VPC with public, private, and database subnets across multiple availability zones

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpc-${var.environment}"
    }
  )
}

# Internet Gateway for public subnet connectivity
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-igw-${var.environment}"
    }
  )
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-public-subnet-${count.index + 1}-${var.environment}"
      Type = "public"
      "kubernetes.io/role/elb" = "1"
    }
  )
}

# Private Subnets (for application workloads)
resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-private-subnet-${count.index + 1}-${var.environment}"
      Type = "private"
      "kubernetes.io/role/internal-elb" = "1"
    }
  )
}

# Database Subnets (isolated subnets for RDS, ElastiCache)
resource "aws_subnet" "database" {
  count             = length(var.database_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.database_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-database-subnet-${count.index + 1}-${var.environment}"
      Type = "database"
    }
  )
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  domain = "vpc"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-nat-eip-${count.index + 1}-${var.environment}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways for private subnet internet access
resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-nat-gw-${count.index + 1}-${var.environment}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-public-rt-${var.environment}"
      Type = "public"
    }
  )
}

# Public Route to Internet Gateway
resource "aws_route" "public_internet_gateway" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# Associate Public Subnets with Public Route Table
resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route Tables for Private Subnets
resource "aws_route_table" "private" {
  count  = var.single_nat_gateway ? 1 : length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-private-rt-${count.index + 1}-${var.environment}"
      Type = "private"
    }
  )
}

# Private Routes to NAT Gateway
resource "aws_route" "private_nat_gateway" {
  count                  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.availability_zones)) : 0
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

# Associate Private Subnets with Private Route Tables
resource "aws_route_table_association" "private" {
  count          = length(var.private_subnet_cidrs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = var.single_nat_gateway ? aws_route_table.private[0].id : aws_route_table.private[count.index].id
}

# Route Table for Database Subnets
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-database-rt-${var.environment}"
      Type = "database"
    }
  )
}

# Associate Database Subnets with Database Route Table
resource "aws_route_table_association" "database" {
  count          = length(var.database_subnet_cidrs)
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# VPC Flow Logs for network monitoring
resource "aws_flow_log" "main" {
  count                = var.enable_flow_logs ? 1 : 0
  iam_role_arn         = var.flow_logs_role_arn
  log_destination      = var.flow_logs_destination
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.main.id
  log_destination_type = var.flow_logs_destination_type

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpc-flow-logs-${var.environment}"
    }
  )
}

# VPC Endpoints for AWS Services (reduces data transfer costs and improves security)
resource "aws_vpc_endpoint" "s3" {
  count        = var.enable_s3_endpoint ? 1 : 0
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${var.region}.s3"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-s3-endpoint-${var.environment}"
    }
  )
}

resource "aws_vpc_endpoint_route_table_association" "s3_private" {
  count           = var.enable_s3_endpoint ? length(var.availability_zones) : 0
  route_table_id  = var.single_nat_gateway ? aws_route_table.private[0].id : aws_route_table.private[count.index].id
  vpc_endpoint_id = aws_vpc_endpoint.s3[0].id
}

resource "aws_vpc_endpoint" "ecr_api" {
  count               = var.enable_ecr_endpoint ? 1 : 0
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [var.vpc_endpoint_security_group_id]
  private_dns_enabled = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-ecr-api-endpoint-${var.environment}"
    }
  )
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  count               = var.enable_ecr_endpoint ? 1 : 0
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [var.vpc_endpoint_security_group_id]
  private_dns_enabled = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-ecr-dkr-endpoint-${var.environment}"
    }
  )
}
