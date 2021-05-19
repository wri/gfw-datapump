resource "aws_sfn_state_machine" "datapump" {
  name       = substr("${local.project}-datapump${local.name_suffix}", 0, 64)
  role_arn   = aws_iam_role.datapump_states.arn
  definition = data.template_file.sfn_datapump.rendered
  tags       = local.tags
}