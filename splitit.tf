variable "aws_region" {
  type = "string"
  default = "us-east-2"
}

provider "aws" {
  region = "${var.aws_region}"
  version = "~> 2.0"

  endpoints {
    dynamodb = "http://localhost:8000/"
  }
}

resource "aws_dynamodb_table" "checks-ddb-table" {
  name          = "SplitItChecks"
  billing_mode  = "PAY_PER_REQUEST"
  hash_key      = "CheckId"

  attribute {
    name = "CheckId"
    type = "S"
  }
}

resource "aws_dynamodb_table" "line-items-ddb-table" {
  name          = "SplitItLineItems"
  billing_mode  = "PAY_PER_REQUEST"
  hash_key      = "LineItemId"

  attribute {
    name = "LineItemId"
    type = "S"
  }
}
