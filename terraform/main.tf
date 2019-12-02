terraform {
  backend "s3" {
    bucket = "gfw-terraform-dev"
    key    = "state/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_iam_policy" "geotrellis_summary_update" {
  name = "geotrellis_summary_update"
  path = "/"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
      {
          "Effect": "Allow",
          "Action": [
              "secretsmanager:GetRandomPassword",
              "lambda:InvokeFunction",
              "secretsmanager:GetResourcePolicy",
              "secretsmanager:GetSecretValue",
              "secretsmanager:DescribeSecret",
              "secretsmanager:ListSecretVersionIds",
              "elasticmapreduce:RunJobFlow",
              "elasticmapreduce:DescribeCluster",
              "cloudformation:DescribeChangeSet",
              "cloudformation:DescribeStackResources",
              "cloudformation:DescribeStacks",
              "cloudformation:GetTemplate",
              "cloudformation:ListStackResources",
              "cloudwatch:*",
              "ec2:DescribeSecurityGroups",
              "ec2:DescribeSubnets",
              "ec2:DescribeVpcs",
              "events:*",
              "iam:GetPolicy",
              "iam:GetPolicyVersion",
              "iam:GetRole",
              "iam:GetRolePolicy",
              "iam:ListAttachedRolePolicies",
              "iam:ListRolePolicies",
              "iam:ListRoles",
              "iam:PassRole",
              "lambda:*",
              "logs:*",
              "s3:*"
          ],
          "Resource": "*"
      }
  ]
}
EOF
}

resource "aws_iam_role" "geotrellis_summary_update_states" {
  name = "geotrellis_summary_update_states"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement":
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "states.us-east-1.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
}
EOF
}

resource "aws_iam_role" "geotrellis_summary_update_lambda" {
  name = "geotrellis_summary_update_lambda"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement":
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
}
EOF
}

resource "aws_iam_role_policy_attachment" "geotrellis_summary_update_lambda" {
    role       = "${aws_iam_role.geotrellis_summary_update_lambda.name}"
    policy_arn = "${aws_iam_policy.geotrellis_summary_update.arn}"
}

resource "aws_iam_role_policy_attachment" "geotrellis_summary_update_states" {
    role       = "${aws_iam_role.geotrellis_summary_update_states.name}"
    policy_arn = "${aws_iam_policy.geotrellis_summary_update.arn}"
}

resource "aws_lambda_function" "submit_job" {
  function_name    = "submit-job_geotrellis-summary-update"
  filename         = "../lambdas/submit_job/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/submit_job/function.zip")}"
  role             = "${aws_iam_role.geotrellis_summary_update_lambda.arn}"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_lambda_function" "upload_results_to_datasets" {
  function_name    = "upload-results-to-datasets_geotrellis-summary-update"
  filename         = "../lambdas/upload_results_to_datasets/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/upload_results_to_datasets/function.zip")}"
  role             = "${aws_iam_role.geotrellis_summary_update_lambda.arn}"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_lambda_function" "check_datasets_saved" {
  function_name    = "check-datasets-saved_geotrellis-summary-update"
  filename         = "../lambdas/check_datasets_saved/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/check_datasets_saved/function.zip")}"
  role             = "${aws_iam_role.geotrellis_summary_update_lambda.arn}"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_lambda_function" "check_new_areas" {
  function_name    = "check-new-areas_geotrellis-summary-update"
  filename         = "../lambdas/check_new_areas/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/check_new_areas/function.zip")}"
  role             = "${aws_iam_role.geotrellis_summary_update_lambda.arn}"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_lambda_function" "update_new_area_statuses" {
  function_name    = "update-new-area-statuses_geotrellis-summary-update"
  filename         = "../lambdas/update_new_area_statuses/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/update_new_area_statuses/function.zip")}"
  role             = "${aws_iam_role.geotrellis_summary_update_lambda.arn}"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_sfn_state_machine" "geotrellis_summary_update" {
  name     = "geotrellis-summary-update"
  role_arn = "${aws_iam_role.geotrellis_summary_update_states.arn}"

  definition = "${file("../step_functions/geotrellis_summary_update.json")}"
}

resource "aws_sfn_state_machine" "summarize_new_areas" {
  name     = "geotrellis-summary-update"
  role_arn = "${aws_iam_role.geotrellis_summary_update_states.arn}"
  definition = "${file("../step_functions/summarize_new_areas.json")}"
}

resource "aws_cloudwatch_event_rule" "everyday-11-pm-est" {
    name = "everyday-11-pm-est"
    description = "Fires every five minutes"
    schedule_expression = "cron(0 4 ? * * *)"
}

resource "aws_cloudwatch_event_target" "nightly-new-area-check" {
    rule = "${aws_cloudwatch_event_rule.everyday-11-pm-est.name}"
    target_id = "summarize_new_areas"
    arn = "${aws_sfn_state_machine.summarize_new_areas.arn}"
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_check_foo" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = "${aws_lambda_function.check_foo.function_name}"
    principal = "events.amazonaws.com"
    source_arn = "${aws_cloudwatch_event_rule.every_five_minutes.arn}"
}