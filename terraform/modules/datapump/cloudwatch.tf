resource "aws_cloudwatch_event_rule" "everyday-11-pm-est" {
  name                = substr("everyday-11-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 11 pm EST"
  schedule_expression = "cron(0 4 ? * * *)" // -5 to EST
}

resource "aws_cloudwatch_event_target" "nightly-fire-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-11-pm-est.name
  target_id = substr("${local.project}-nightly-fire-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}