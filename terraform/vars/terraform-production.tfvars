environment = "production"

lambda_submit_job_runtime     = "python3.7"
lambda_submit_job_memory_size = 1024
lambda_submit_job_timeout     = 300

lambda_upload_results_runtime     = "python3.7"
lambda_upload_results_memory_size = 1024
lambda_upload_results_timeout     = 300

lambda_check_datasets_runtime     = "python3.7"
lambda_check_datasets_memory_size = 1024
lambda_check_datasets_timeout     = 300

lambda_check_new_aoi_runtime     = "python3.7"
lambda_check_new_aoi_memory_size = 3008
lambda_check_new_aoi_timeout     = 900

lambda_update_new_aoi_statuses_runtime     = "python3.7"
lambda_update_new_aoi_statuses_memory_size = 3008
lambda_update_new_aoi_statuses_timeout     = 900

lambda_check_new_glad_alerts_runtime     = "python3.7"
lambda_check_new_glad_alerts_memory_size = 1024
lambda_check_new_glad_alerts_timeout     = 300

lambda_get_latest_fire_alerts_runtime     = "python3.7"
lambda_get_latest_fire_alerts_memory_size = 3008
lambda_get_latest_fire_alerts_timeout     = 900

data_api_viirs_version = "v202010"

geotrellis_jar = "s3://gfw-pipelines/geotrellis/jars/treecoverloss-assembly-1.4.3.jar"

datasets = {
  "geostore": {
    "annualupdate_minimal": {
      "change" = ["eb5d50f5-7219-4638-a72d-802d4b163523"]
      "summary" = ["d0f64f57-a3e2-4362-8dae-ba8f6480bc41"]
      "whitelist" = ["64d80e29-2e7f-4b9c-bef2-dde2241d363e"]
    }
    "gladalerts": {
      "daily_alerts" = ["f914e18d-732d-4b24-a8f6-68a4a8d1c266"]
      "weekly_alerts" = ["189ab09e-50e8-4072-b805-d7bfc9f6f3f9"]
      "summary" = ["7a244c8f-7c98-49d9-990f-3104315a3067"]
      "whitelist" = ["f3ea601e-8aee-4616-a448-3ce43c4c6aa8"]
    }
    "firealerts_viirs": {
      "daily_alerts" = ["0ae3e77e-6af8-44cf-a89f-a2dd0c14fa0f"]
      "weekly_alerts" = ["8c701997-d0b1-4365-b8a4-35376c0a486d"]
      "whitelist" = ["254cb7f6-e396-49b7-9966-06ce5d94c00a"]
    }
    "firealerts_modis": {
      "daily_alerts" = ["6e811935-6b20-4be1-8b96-f258216a5a8b"]
      "weekly_alerts" = ["c25ae976-1433-48e1-9f71-7d248162828e"]
      "whitelist" = ["cf00c4da-aac0-4071-bd23-73f647844031"]
    }
  }
  "gadm": {
    "gladalerts": {
      "iso": {
        "weekly_alerts" = ["c9339da7-871e-46cc-b94d-9d98275c9c26"]
      }
      "adm1": {
        "weekly_alerts" = ["5831c6d8-08d1-46c0-bf8f-d0a77c47c379"]
      }
      "adm2": {
        "daily_alerts" = ["4b5effbb-d83f-45b9-8bcb-e11cabafc923"]
        "weekly_alerts" = ["71bd928c-71c5-4453-a85b-393ef10cfc74"]
      }
    }
    "firealerts_viirs": {
      "all" = ["7af31612-a88a-4910-9b11-88c355b2f7a4"]
      "iso": {
        "weekly_alerts" = ["f97c9ab9-8322-4ee8-a9d9-cb94242811dd"]
      }
      "adm1": {
        "weekly_alerts" = ["54bb00e8-9888-494a-bcd8-9fd3760fe384"]
      }
      "adm2": {
        "daily_alerts" = ["1c72bdb6-0f93-4319-bf47-e2f23c5f0e37"]
        "weekly_alerts" = ["ff88e67c-2a94-438d-bfd0-4f4c04f68860"]
      }
    }
    "firealerts_modis": {
      "iso": {
        "weekly_alerts" = ["6cf67766-fea4-4111-b236-9defa916f91e"]
      }
      "adm1": {
        "weekly_alerts" = ["cae03a7a-6a37-47cc-99ca-04c43428986f"]
      }
      "adm2": {
        "daily_alerts" = ["ff7671ff-3bbd-4ca8-b136-b164784991e6"]
        "weekly_alerts" = ["83bd3bbc-324e-4c6b-8761-614b1da26308"]
      }
    }
  }
  "wdpa": {
    "gladalerts": {
      "daily_alerts" = ["8df930b8-7215-4d69-922e-78c597c911a0"]
      "weekly_alerts" = ["67cead8c-14c0-40bd-b4b7-075869e075df"]
    }
    "firealerts_modis": {
      "daily_alerts" = ["32ce0de7-7c5c-4b3c-a60d-ca2b3e4f2822"]
      "weekly_alerts" = ["a2dcdee5-06d2-4dfd-a811-591966f8639b"]
    }
    "firealerts_viirs": {
      "daily_alerts" = ["3001b513-52f5-4f58-bc92-e7f725f8aa49"]
      "weekly_alerts" = ["cfd2a045-54c6-4713-bf3e-b312bca86b29"]
    }
  }
}