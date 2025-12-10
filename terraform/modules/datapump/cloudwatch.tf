# Time in the text are all PST (Pacific Standard Time).
# The hours in the cron() expression are in UTC.

resource "aws_cloudwatch_event_rule" "everyday-6-pm-pst" {
  name                = substr("everyday-6-pm-pst${local.name_suffix}", 0, 64)
  description         = "Run everyday at 6 pm PST"
  schedule_expression = "cron(0 2 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-5-pm-pst" {
  name                = substr("everyday-5-pm-pst${local.name_suffix}", 0, 64)
  description         = "Run everyday at 5 pm PST"
  schedule_expression = "cron(0 1 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-2-pm-pst" {
  name                = substr("everyday-2-pm-pst${local.name_suffix}", 0, 64)
  description         = "Run everyday at 2 pm PST"
  schedule_expression = "cron(0 22 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-230-am-pst" {
  name                = substr("everyday-230-am-pst${local.name_suffix}", 0, 64)
  description         = "Run everyday at 230 am PST"
  schedule_expression = "cron(30 10 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-11-am-pst" {
  name                = substr("everyday-11-am-pst${local.name_suffix}", 0, 64)
  description         = "Run everyday at 11 am PST"
  schedule_expression = "cron(0 19 ? * * *)"
  tags                = local.tags
}

# The count condition in each of the resources below ensures that the CloudWatch
# events only happen in production.

# Nightly runs start at 2pm PST
resource "aws_cloudwatch_event_target" "sync-areas" {
  rule      = aws_cloudwatch_event_rule.everyday-2-pm-pst.name
  target_id = substr("${local.project}-sync-areas${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input     = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"rw_areas\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "sync-deforestation-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-2-pm-pst.name
  target_id = substr("${local.project}-sync-deforestation-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input     = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"wur_radd_alerts\", \"umd_glad_landsat_alerts\", \"umd_glad_sentinel2_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "sync-glad" {
  rule      = aws_cloudwatch_event_rule.everyday-5-pm-pst.name
  target_id = substr("${local.project}-sync-glad${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"glad\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "sync-viirs" {
  rule      = aws_cloudwatch_event_rule.everyday-6-pm-pst.name
  target_id = substr("${local.project}-sync-viirs${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"viirs\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "sync-modis" {
  rule      = aws_cloudwatch_event_rule.everyday-6-pm-pst.name
  target_id = substr("${local.project}-sync-modis${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"modis\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

# Run every day at 6pm PST. It should run after the deforestation alerts above are complete
# (which always finish in 2.5 hours, so running 4 hours after is fine.)
resource "aws_cloudwatch_event_target" "sync-integrated-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-6-pm-pst.name
  target_id = substr("${local.project}-sync-integrated-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"integrated_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

# Run every day at 11am PST, but new data from UMD should only be available on Saturday morning,
# so should only do a full run generating a new version once a week on Saturday/Sunday.
resource "aws_cloudwatch_event_target" "sync-dist-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-11-am-pst.name
  target_id = substr("${local.project}-sync-umd-glad-dist-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"umd_glad_dist_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

# Run every day at 2:30am PST. It should run after the integrated alerts is complete
# (which finishes in 7-8.5 hours.)
resource "aws_cloudwatch_event_target" "sync-integrated-dist-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-230-am-pst.name
  target_id = substr("${local.project}-sync-integrated-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"gfw_integrated_dist_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}
