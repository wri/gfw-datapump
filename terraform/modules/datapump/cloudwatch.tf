resource "aws_cloudwatch_event_rule" "everyday-11-pm-est" {
  name                = substr("everyday-11-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 11 pm EST"
  schedule_expression = "cron(0 4 ? * * *)" // -5 to EST
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-9-pm-est" {
  name                = substr("everyday-9-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 9 pm EST"
  schedule_expression = "cron(0 2 ? * * *)" // -5 to EST
  tags                = local.tags
}

resource "aws_cloudwatch_event_target" "nightly-sync-areas" {
  rule      = aws_cloudwatch_event_rule.everyday-9-pm-est.name
  target_id = substr("${local.project}-nightly-sync-areas${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input     = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"rw_areas\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "nightly-sync" {
  rule      = aws_cloudwatch_event_rule.everyday-11-pm-est.name
  target_id = substr("${local.project}-nightly-sync${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"glad\", \"viirs\", \"modis\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}