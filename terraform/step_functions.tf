resource "aws_sfn_state_machine" "geotrellis_summary_update" {
  name       = "geotrellis-summary-update${local.name_suffix}"
  role_arn   = aws_iam_role.geotrellis_summary_update_states.arn
  definition = data.template_file.sfn_geotrellis_summary_update.rendered
}

resource "aws_sfn_state_machine" "summarize_new_areas" {
  name       = "summarize-new-areas${local.name_suffix}"
  role_arn   = aws_iam_role.geotrellis_summary_update_states.arn
  definition = data.template_file.sfn_summarize_new_areas.rendered
}