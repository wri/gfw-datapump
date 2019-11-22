pushd venvpy/lib/python3.7/site-packages && zip -r9 base_function.zip .
popd

cp venvpy/lib/python3.7/site-packages/base_function.zip lambdas/submit_job/function.zip
cp venvpy/lib/python3.7/site-packages/base_function.zip lambdas/upload_results_to_datasets/function.zip
cp venvpy/lib/python3.7/site-packages/base_function.zip lambdas/check_datasets_saved/function.zip

zip -g lambdas/submit_job/function.zip lambdas/submit_job/function.py
zip -g lambdas/upload_results_to_datasets/function.zip lambdas/upload_results_to_datasets/function.py
zip -g lambdas/check_datasets_saved/function.zip lambdas/check_datasets_saved/function.py

rm venvpy/lib/python3.7/site-packages/base_function.zip
