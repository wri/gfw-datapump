resource "aws_cloudwatch_event_rule" "everyday-11-pm-est" {
  name                = substr("everyday-11-pm-est${local.name_suffix}", 0, 64)
  description         = "Fires every five minutes"
  schedule_expression = "cron(0 4 ? * * *)" // -5 to EST
}

//We only want to schedule this event in production
resource "aws_cloudwatch_event_target" "nightly-new-area-check" {
  rule      = aws_cloudwatch_event_rule.everyday-11-pm-est.name
  target_id = substr("${local.project}-summarize_new_areas${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.new_user_aoi.id
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}