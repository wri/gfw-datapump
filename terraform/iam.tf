resource "aws_iam_policy" "geotrellis_summary_update" {
  name   = "geotrellis_summary_update"
  path   = "/"
  policy = data.template_file.geotrellis_summary_update.rendered
}

resource "aws_iam_role" "geotrellis_summary_update_states" {
  name               = "geotrellis_summary_update_states"
  assume_role_policy = data.template_file.sts_assume_role_states.rendered
}

resource "aws_iam_role" "geotrellis_summary_update_lambda" {
  name               = "geotrellis_summary_update_lambda"
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
