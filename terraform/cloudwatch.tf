resource "aws_cloudwatch_event_rule" "everyday-11-pm-est" {
  name                = "everyday-11-pm-est"
  description         = "Fires every five minutes"
  schedule_expression = "cron(0 4 ? * * *)"
}

resource "aws_cloudwatch_event_target" "nightly-new-area-check" {
  rule      = aws_cloudwatch_event_rule.everyday-11-pm-est.name
  target_id = "summarize_new_areas"
  arn       = aws_sfn_state_machine.summarize_new_areas.id
  role_arn  = aws_iam_role.geotrellis_summary_update_states.arn
}