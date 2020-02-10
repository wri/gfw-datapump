resource "aws_sfn_state_machine" "geotrellis_dataset" {
  name       = substr("${local.project}-geotrellis_dataset${local.name_suffix}", 0, 64)
  role_arn   = aws_iam_role.datapump_states.arn
  definition = data.template_file.sfn_geotrellis_summary_update.rendered
}

resource "aws_sfn_state_machine" "new_user_aoi" {
  name       = substr("${local.project}-new_user_aoi${local.name_suffix}", 0, 64)
  role_arn   = aws_iam_role.datapump_states.arn
  definition = data.template_file.sfn_summarize_new_aoi.rendered
}

resource "aws_sfn_state_machine" "new_glad_alerts" {
  name       = substr("${local.project}-new_glad_alerts${local.name_suffix}", 0, 64)
  role_arn   = aws_iam_role.datapump_states.arn
  definition = data.template_file.sfn_summarize_new_glad_alerts.rendered
}