resource "aws_iam_policy" "geotrellis_summary_update" {
  name   = "aoi${local.name_suffix}"
  path   = "/"
  policy = data.template_file.geotrellis_summary_update.rendered
}

resource "aws_iam_role" "geotrellis_summary_update_states" {
  name               = "aoi_update_states${local.name_suffix}"
  assume_role_policy = data.template_file.sts_assume_role_states.rendered
}

resource "aws_iam_role" "geotrellis_summary_update_lambda" {
  name               = "aoi_summary_update_lambda${local.name_suffix}"
  assume_role_policy = data.template_file.sts_assume_role_lambda.rendered
}

resource "aws_iam_role_policy_attachment" "geotrellis_summary_update_lambda" {
  role       = aws_iam_role.geotrellis_summary_update_lambda.name
  policy_arn = aws_iam_policy.geotrellis_summary_update.arn
}

resource "aws_iam_role_policy_attachment" "geotrellis_summary_update_states" {
  role       = aws_iam_role.geotrellis_summary_update_states.name
  policy_arn = aws_iam_policy.geotrellis_summary_update.arn
}
