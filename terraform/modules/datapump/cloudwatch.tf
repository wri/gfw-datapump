# Note: when it says est/EST here, it really means PST (Pacific Standard time)
# The hours in the cron() expression are in UTC.

resource "aws_cloudwatch_event_rule" "everyday-11-pm-est" {
  name                = substr("everyday-11-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 11 pm EST"
  schedule_expression = "cron(0 7 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-10-pm-est" {
  name                = substr("everyday-10-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 10 pm EST"
  schedule_expression = "cron(0 6 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-7-pm-est" {
  name                = substr("everyday-7-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 7 pm EST"
  schedule_expression = "cron(0 3 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-830-am-est" {
  name                = substr("everyday-830-am-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 830 am EST"
  schedule_expression = "cron(30 16 ? * * *)"
  tags                = local.tags
}

resource "aws_cloudwatch_event_rule" "everyday-1-pm-est" {
  name                = substr("everyday-1-pm-est${local.name_suffix}", 0, 64)
  description         = "Run everyday at 1 pm EST"
  schedule_expression = "cron(0 21 ? * * *)"
  tags                = local.tags
}

# The count condition in each of the resources below ensures that the CloudWatch
# events only happen in production.
resource "aws_cloudwatch_event_target" "sync-areas" {
  rule      = aws_cloudwatch_event_rule.everyday-7-pm-est.name
  target_id = substr("${local.project}-sync-areas${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input     = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"rw_areas\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "sync-deforestation-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-7-pm-est.name
  target_id = substr("${local.project}-sync-deforestation-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input     = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"wur_radd_alerts\", \"umd_glad_landsat_alerts\", \"umd_glad_sentinel2_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "sync-glad" {
  rule      = aws_cloudwatch_event_rule.everyday-10-pm-est.name
  target_id = substr("${local.project}-sync-glad${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"glad\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "sync-viirs" {
  rule      = aws_cloudwatch_event_rule.everyday-11-pm-est.name
  target_id = substr("${local.project}-sync-viirs${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"viirs\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

resource "aws_cloudwatch_event_target" "sync-modis" {
  rule      = aws_cloudwatch_event_rule.everyday-11-pm-est.name
  target_id = substr("${local.project}-sync-modis${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"modis\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

# Run every day at 11pm PST. It should run after the deforestation alerts above are complete
# (which always finish in 2.5 hours, so running 4 hours after is fine.)
resource "aws_cloudwatch_event_target" "sync-integrated-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-11-pm-est.name
  target_id = substr("${local.project}-sync-integrated-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"integrated_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

# Run every day at 1pm PST, but new data from UMD should only be available on Saturday morning,
# so should only do a full run generating a new version once a week on Saturday/Sunday.
resource "aws_cloudwatch_event_target" "sync-dist-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-1-pm-est.name
  target_id = substr("${local.project}-sync-umd-glad-dist-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"umd_glad_dist_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}

# Run every day at 8:30am PST. It should run after the integrated alerts is complete
# (which finishes in 7-8.5 hours.)
resource "aws_cloudwatch_event_target" "sync-integrated-dist-alerts" {
  rule      = aws_cloudwatch_event_rule.everyday-830-am-est.name
  target_id = substr("${local.project}-sync-integrated-alerts${local.name_suffix}", 0, 64)
  arn       = aws_sfn_state_machine.datapump.id
  input    = "{\"command\": \"sync\", \"parameters\": {\"types\": [\"gfw_integrated_dist_alerts\"]}}"
  role_arn  = aws_iam_role.datapump_states.arn
  count     = var.environment == "production" ? 1 : 0
}
