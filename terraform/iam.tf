resource "aws_iam_policy" "datapump" {
  name   = "${local.project}-${local.name_suffix}"
  path   = "/"
  policy = data.template_file.geotrellis_summary_update.rendered
}

resource "aws_iam_role" "datapump_states" {
  name               = "${local.project}-states${local.name_suffix}"
  assume_role_policy = data.template_file.sts_assume_role_states.rendered
}

resource "aws_iam_role" "datapump_lambda" {
  name               = "${local.project}-lambda${local.name_suffix}"
  assume_role_policy = data.template_file.sts_assume_role_lambda.rendered
}

resource "aws_iam_role_policy_attachment" "datapump_lambda" {
  role       = aws_iam_role.datapump_lambda.name
  policy_arn = aws_iam_policy.datapump.arn
}

resource "aws_iam_role_policy_attachment" "datapump_states" {
  role       = aws_iam_role.datapump_states.name
  policy_arn = aws_iam_policy.datapump.arn
}
