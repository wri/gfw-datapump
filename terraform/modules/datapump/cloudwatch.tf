resource "aws_cloudwatch_event_rule" "everyday-11-pm-est" {
  name                = substr("everyday-11-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 11 pm EST"
  schedule_expression = "cron(0 7 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-7-pm-est" {
  name                = substr("everyday-7-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 7 pm EST"
  schedule_expression = "cron(0 3 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-3-am-est" {
  name                = substr("everyday-3-am-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 3 am EST"
  schedule_expression = "cron(0 11 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_target" "nightly-sync-areas" {
  rule      = aws_cloudwatch_event_rule.everyday-7-pm-est.name
  target_id = substr("${local.project}-nightly-sync-areas${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input     = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"rw_areas\", \"wur_radd_alerts\", \"umd_glad_landsat_alerts\", \"umd_glad_sentinel2_alerts\"]}}"
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

resource "aws_cloudwatch_event_target" "nightly-sync-integrated" {
  rule      = aws_cloudwatch_event_rule.everyday-3-am-est.name
  target_id = substr("${local.project}-nightly-sync${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"integrated_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}