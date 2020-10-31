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

lambda_get_latest_fire_alerts_runtime     = "python3.6"
lambda_get_latest_fire_alerts_memory_size = 3008
lambda_get_latest_fire_alerts_timeout     = 900

data_api_viirs_version = "v202010"

geotrellis_jar = "s3://gfw-pipelines/geotrellis/jars/treecoverloss-assembly-1.2.1.jar"

datasets = {
  "geostore": {
    "annualupdate_minimal": {
      "change" = ["ecb4817b-a09e-4c78-b735-617e93a7ff4c", "eb5d50f5-7219-4638-a72d-802d4b163523"]
      "summary" = ["b2603f43-8349-4401-99d3-2fb56f889388", "d0f64f57-a3e2-4362-8dae-ba8f6480bc41"]
      "whitelist" = ["28006d70-42b5-4034-9008-505806101863", "64d80e29-2e7f-4b9c-bef2-dde2241d363e"]
    }
    "gladalerts": {
      "daily_alerts" = ["bd35ab8e-1810-4eda-981e-5f0e6fe76f74", "f914e18d-732d-4b24-a8f6-68a4a8d1c266"]
      "weekly_alerts" = ["95735f8d-b86b-485a-8766-c480dd4da21d", "189ab09e-50e8-4072-b805-d7bfc9f6f3f9"]
      "summary" = ["11454c79-e0ac-4c58-90ee-dcc9d9d30031", "7a244c8f-7c98-49d9-990f-3104315a3067"]
      "whitelist" = ["61d9f9bc-883c-4c70-865a-af8126c7ccee", "f3ea601e-8aee-4616-a448-3ce43c4c6aa8"]
    }
    "firealerts_viirs": {
      "daily_alerts" = ["b7bf28ef-e893-47da-844a-25a46115fe34", "0ae3e77e-6af8-44cf-a89f-a2dd0c14fa0f"]
      "weekly_alerts" = ["1f7bb181-7b28-4823-8aa5-28335268f961", "8c701997-d0b1-4365-b8a4-35376c0a486d"]
      "whitelist" = ["d7d9a4b0-e295-42a8-bd46-fb48981c1eca", "254cb7f6-e396-49b7-9966-06ce5d94c00a"]
    }
    "firealerts_modis": {
      "daily_alerts" = ["825edfcd-07f4-4b2b-9054-282663c60caa", "6e811935-6b20-4be1-8b96-f258216a5a8b"]
      "weekly_alerts" = ["cfd880fd-8b81-46c2-b3e3-84ba22955337", "c25ae976-1433-48e1-9f71-7d248162828e"]
      "whitelist" = ["e101f15a-4104-4dfd-bade-164986154694", "cf00c4da-aac0-4071-bd23-73f647844031"]
    }
  }
  "gadm": {
    "gladalerts": {
      "iso": {
        "weekly_alerts" = ["2c444b8d-991a-4e90-bb18-6d9063be1432", "c9339da7-871e-46cc-b94d-9d98275c9c26"]
      }
      "adm1": {
        "weekly_alerts" = ["094ae08c-3bf2-4d85-830e-e6d4cbc5c05d", "5831c6d8-08d1-46c0-bf8f-d0a77c47c379"]
      }
      "adm2": {
        "daily_alerts" = ["2cacc2dc-35d6-46ab-8641-384267b8ba64", "4b5effbb-d83f-45b9-8bcb-e11cabafc923"]
        "weekly_alerts" = ["6476cd26-446a-4bc0-add5-79baeecceb12", "71bd928c-71c5-4453-a85b-393ef10cfc74"]
      }
    }
    "firealerts_viirs": {
      "all" = ["76642243-d895-48f7-b8e8-5333851bd00f", "7af31612-a88a-4910-9b11-88c355b2f7a4a"]
      "iso": {
        "weekly_alerts" = ["4625ce33-4046-49e3-9861-86d9b1832710", "f97c9ab9-8322-4ee8-a9d9-cb94242811dd"]
      }
      "adm1": {
        "weekly_alerts" = ["0759c142-3a10-445e-a0f8-7e2c61c23344", "54bb00e8-9888-494a-bcd8-9fd3760fe384"]
      }
      "adm2": {
        "daily_alerts" = ["c1bb5e10-4da9-4776-8362-ab48a746fcb5", "1c72bdb6-0f93-4319-bf47-e2f23c5f0e37"]
        "weekly_alerts" = ["13b5df89-abdd-4235-9cd0-accd1c38f11a", "ff88e67c-2a94-438d-bfd0-4f4c04f68860"]
      }
    }
    "firealerts_modis": {
      "iso": {
        "weekly_alerts" = ["9801eea9-6cbc-4d93-9845-de6fa267fbae", "6cf67766-fea4-4111-b236-9defa916f91e"]
      }
      "adm1": {
        "weekly_alerts" = ["29aec1f5-7f76-4b44-bd4b-61fb803765ee", "cae03a7a-6a37-47cc-99ca-04c43428986f"]
      }
      "adm2": {
        "daily_alerts" = ["269af948-fc1c-40d7-823b-35bdb75c67ad", "ff7671ff-3bbd-4ca8-b136-b164784991e6"]
        "weekly_alerts" = ["724293e5-8eac-4b7e-b7fb-e190db2633a0", "83bd3bbc-324e-4c6b-8761-614b1da26308"]
      }
    }
  }
  "wdpa": {
    "gladalerts": {
      "daily_alerts" = ["bfb86d53-c8de-46c5-a424-94eb63fea6da", "8df930b8-7215-4d69-922e-78c597c911a0"]
      "weekly_alerts" = ["8b7240e7-8372-4b6e-9aed-4694c7a46b49", "67cead8c-14c0-40bd-b4b7-075869e075df"]
    }
    "firealerts_modis": {
      "daily_alerts" = ["46aa211a-f1e7-491c-af26-1dfcf1e88c91", "32ce0de7-7c5c-4b3c-a60d-ca2b3e4f2822"]
      "weekly_alerts" = ["30575408-697b-4151-b430-d54462b54cc9", "a2dcdee5-06d2-4dfd-a811-591966f8639b"]
    }
    "firealerts_viirs": {
      "daily_alerts" = ["a8575b2f-5035-4855-85e8-a16255aed666", "3001b513-52f5-4f58-bc92-e7f725f8aa49"]
      "weekly_alerts" = ["eeb586f8-0ea7-4f76-a5b3-2e5bc8cabcbf", "cfd2a045-54c6-4713-bf3e-b312bca86b29"]
    }
  }
}