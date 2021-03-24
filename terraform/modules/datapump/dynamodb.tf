resource "aws_dynamodb_table" "datapump" {
  name           = substr("${local.project}-datapump${local.name_suffix}", 0, 64)
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }
}