resource "aws_cloudwatch_event_rule" "everyday-11-pm-est" {
  name                = substr("everyday-11-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 11 pm EST"
  schedule_expression = "cron(0 4 ? * * *)" // -5 to EST
}

resource "aws_cloudwatch_event_rule" "everyday-3-am-est" {
  name                = substr("everyday-3-am-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 3 am EST"
  schedule_expression = "cron(0 8 ? * * *)" // -5 to EST
}

//We only want to schedule this event in production
resource "aws_cloudwatch_event_target" "nightly-new-area-check" {
  rule      = aws_cloudwatch_event_rule.everyday-11-pm-est.name
  target_id = substr("${local.project}-nightly-new-area-check${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.new_user_aoi.id
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" || var.environment == "staging" ? 1 : 0
}

//We only want to schedule this event in production
resource "aws_cloudwatch_event_target" "nightly-new-glad-alerts-check" {
  rule      = aws_cloudwatch_event_rule.everyday-3-am-est.name
  target_id = substr("${local.project}-nightly-new-glad-alerts-check${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.new_glad_alerts.id
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" || var.environment == "staging"? 1 : 0
}