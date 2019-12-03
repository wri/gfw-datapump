import os


from lambdas.upload_results_to_datasets.lambda_function import handler

os.environ["ENV"] = "test"


def test_handler():
    NotImplementedError()
